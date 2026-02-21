from shellphish_crs_utils.models.oss_fuzz import AugmentedProjectMetadata
from shellphish_crs_utils.oss_fuzz.project import OSSFuzzProject


class TargetProject:
    """
    Thin standalone abstraction over the existing project runtime object.
    This keeps call sites decoupled from framework naming while preserving behavior.
    """

    def __init__(self, project: OSSFuzzProject):
        self._project = project

    @classmethod
    def from_oss_fuzz(
        cls,
        project_id: str,
        oss_fuzz_project_path: str,
        augmented_metadata: AugmentedProjectMetadata,
        use_task_service: bool = False,
    ) -> "TargetProject":
        project = OSSFuzzProject(
            project_id=project_id,
            oss_fuzz_project_path=oss_fuzz_project_path,
            augmented_metadata=augmented_metadata,
            use_task_service=use_task_service,
        )
        return cls(project)

    def __getattr__(self, name):
        return getattr(self._project, name)
