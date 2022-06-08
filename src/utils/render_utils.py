from typing import Callable
import bpy
from bpy.types import Context

# Cycles types are generated by the python API at runtime, so aren't accessible for static typing https://developer.blender.org/T68050#848508
from cycles.properties import CyclesPreferences, CyclesRenderSettings


def get_config_resetter(context: Context = bpy.context) -> Callable[[Context], None]:
    """
    Get a function that will reset the render engine to whatever settings it is currently using. This can be useful to call before configuring the render engine, so it can be reset for the user after usage.

    :param context: The current execution Context.
    """

    reset = lambda ctx: None

    def reset_cb(ctx: Context) -> None:
        """
        Reset the render engine settings for the given context to whatever it was are at the time this function was created

        :param context: The current execution Context.
        """
        reset(ctx)

    if context.scene.render.engine == "CYCLES":
        cycles_settings: CyclesRenderSettings = context.scene.cycles
        cycles_prefs: CyclesPreferences = context.preferences.addons[
            "cycles"
        ].preferences

        reset = lambda ctx: configure_cycles(
            context=ctx,
            mode=cycles_settings.device,
            feature_set=cycles_settings.feature_set,
            device_type=cycles_prefs.compute_device_type,
            samples=cycles_settings.samples,
            denoise=cycles_settings.use_denoising,
        )

    return reset_cb


def configure_cycles(
    context: Context = bpy.context,
    mode: str = "GPU",
    feature_set: str = "SUPPORTED",
    device_type="CUDA",
    samples: int = 4096,
    denoise: bool = True,
) -> None:
    """
    Activate and configure the Cycles rendering engine for rendering.

    :param context: The execution context to configure Cycles for.
    :param mode: The prefered rendering mode. Must be `"GPU"`, `"CPU"` or `"HYBRID"`.
    :param feature_set: The Cycles feature set to use.
    :param device_type: The GPU API to use for rendering. Should be `"CUDA"` or `"OPTIX"`. This will be internally applied as `"CUDA"` if running in `"HYBRID"` mode
    :param samples: The number of samples per frame.
    :param samples: Toggle denoising.
    """

    # Activate Cycles rendering engine
    context.scene.render.engine = "CYCLES"

    # Configure Cycles rendering engine
    cycles_settings: CyclesRenderSettings = context.scene.cycles
    cycles_settings.samples = samples
    cycles_settings.use_denoising = denoise
    if mode == "GPU" or mode == "HYBRID":
        cycles_settings.device = "GPU"
    else:
        cycles_settings.device = "CPU"

    cycles_settings.feature_set = feature_set
    if mode == "GPU":
        cycles_settings.tile_size = 256
    else:
        cycles_settings.tile_size = 16

    cycles_prefs: CyclesPreferences = context.preferences.addons["cycles"].preferences
    if mode == "CPU" or mode == "HYBRID":
        cycles_prefs.compute_device_type = "CUDA"
    else:
        cycles_prefs.compute_device_type = device_type

    #########################################
    # Enable only desired rendering devices #
    #########################################

    # (1) Disable all rendering devices
    for device in cycles_prefs.devices:
        device.use = mode == "HYBRID"
    if mode == "HYBRID":
        return

    # (2) has_active_device() will return True if there is a GPU enabled, so we toggle all devices and test if has_active_device() reports them as a GPU or not.
    devs = []
    for device in cycles_prefs.devices:
        device.use = True
        if (mode == "GPU" and cycles_prefs.has_active_device()) or (
            mode == "CPU" and not cycles_prefs.has_active_device()
        ):
            devs.append(device)
        device.use = False
    # (3) Enable all desired devices
    for dev in devs:
        dev.use = True
