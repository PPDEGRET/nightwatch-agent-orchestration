class NightwatchError(Exception):
    """Base error for actionable Nightwatch failures."""


class ValidationError(NightwatchError):
    """A brief or record failed validation."""

    def __init__(self, errors: list[str] | str):
        self.errors = [errors] if isinstance(errors, str) else errors
        super().__init__("; ".join(self.errors))


class InvalidTransition(NightwatchError):
    """A task attempted an invalid queue-state transition."""


class RunnerFailure(NightwatchError):
    """A runner failed a bounded task attempt."""


class RunnerTimeout(RunnerFailure):
    """A runner exceeded the task timeout."""


class RunnerStopped(RunnerFailure):
    """A runner was cooperatively stopped."""


class RunnerCleanupFailure(RunnerFailure):
    """A runner process tree could not be proven terminated; retries must stop."""


class ExternalExecutionDisabled(NightwatchError):
    """External execution was requested without both safety approvals."""
