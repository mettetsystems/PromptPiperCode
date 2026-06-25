from fastapi import APIRouter, Depends

from prompt_piper_api.config import Settings, get_settings
from prompt_piper_api.schemas.inference import InferenceSettingsResponse, to_inference_settings
from prompt_piper_api.schemas.user_settings import (
    UserSettingsResponse,
    UserSettingsUpdateRequest,
    to_user_settings,
    to_user_settings_response,
)
from prompt_piper_api.services.user_settings_service import UserSettingsService, get_user_settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


def get_user_settings_service_dep() -> UserSettingsService:
    return get_user_settings_service()


@router.get("/inference", response_model=InferenceSettingsResponse)
def get_inference_settings(
    settings: Settings = Depends(get_settings),
    user_settings: UserSettingsService = Depends(get_user_settings_service_dep),
) -> InferenceSettingsResponse:
    response = to_inference_settings(settings, user_settings=user_settings)
    return response


@router.get("/user", response_model=UserSettingsResponse)
def get_user_settings(
    settings: Settings = Depends(get_settings),
    user_settings: UserSettingsService = Depends(get_user_settings_service_dep),
) -> UserSettingsResponse:
    return to_user_settings_response(user_settings.load(), settings)


@router.put("/user", response_model=UserSettingsResponse)
def update_user_settings(
    payload: UserSettingsUpdateRequest,
    settings: Settings = Depends(get_settings),
    user_settings: UserSettingsService = Depends(get_user_settings_service_dep),
) -> UserSettingsResponse:
    saved = user_settings.update(to_user_settings(payload))
    return to_user_settings_response(saved, settings)
