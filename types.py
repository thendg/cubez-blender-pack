import bpy_types
from typing import Optional, Type
from bpy.types import Context, Event, Operator


class CubezOperator(Operator):
    bl_idname: str
    bl_label: str
    menu_target: Optional[Type[bpy_types.Menu]] = None

    def error(self, message="Operation failed.") -> set[str]:
        """
        Report an error to Blender.
        Returns `{"CANCELLED"}`, so the return value of this function can be returned out of the operator.

        :param message: The error message to report.
        """

        self.report({"ERROR"}, message)
        return {"CANCELLED"}

    def invoke(self, context: Context, event: Event) -> set[str]:
        """
        Invoke the operator. This method is called before `execute()`, so can be used to setup initialise the operator by setting up
        it's feilds before `execute()` is run.

        :param context: The context in which the operator was invoked.
        :param event: The window event created when the operator was invoked.

        Returns `{"FINISHED"}` if the export completed successfully, {"CANCELLED"} otherwise.
        """
        pass

    def execute(self, context: Context) -> set[str]:
        """
        Execute the operator's business logic.

        :param context: The context in which the operator was executed.

        Returns `{"FINISHED"}` if the export completed successfully, `{"CANCELLED"}` otherwise.
        """
        pass
