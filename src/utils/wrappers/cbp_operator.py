from bpy.types import Context, Event, Operator


class CBPOperator(Operator):
    """
    A wrapper for `bpy.types.Operator` with some added helper methods and better docstrings/typing.
    """

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
        it's fields before `execute()` is run. `invoke()` should not execute any Blender operations, so that it can be quit from cleanly
        with the assurance that the blend file was not affected.

        :param context: The context in which the operator was invoked.
        :param event: The window event created when the operator was invoked.
        """
        return {"FINISHED"}

    def execute(self, context: Context) -> set[str]:
        """
        Execute the operator's business logic.

        :param context: The context in which the operator was executed.

        Returns `{"FINISHED"}` if the export completed successfully, `{"CANCELLED"}` otherwise.
        """
        return {"FINISHED"}
