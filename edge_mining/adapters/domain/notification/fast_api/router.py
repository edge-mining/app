"""API Router for notification domain"""

import uuid
from typing import Annotated, Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.notification.schemas import (
    NOTIFICATION_CONFIG_SCHEMA_MAP,
    NotifierCreateSchema,
    NotifierSchema,
    NotifierUpdateSchema,
)

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import (
    get_adapter_service,
    get_config_service,
)
from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    ConfigurationServiceInterface,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.exceptions import (
    NotifierAlreadyExistsError,
    NotifierConfigurationError,
    NotifierNotFoundError,
)
from edge_mining.shared.interfaces.config import Configuration, NotificationConfig

router = APIRouter()


@router.get("/notifiers", response_model=List[NotifierSchema])
async def get_notifiers_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[NotifierSchema]:
    """Get a list of all configured notifiers."""
    try:
        notifiers = config_service.list_notifiers()

        # Convert to notifier schema
        notifier_schemas: List[NotifierSchema] = []

        for notifier in notifiers:
            notifier_schemas.append(NotifierSchema.from_model(notifier))

        return notifier_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/notifiers/types", response_model=List[NotificationAdapter])
async def get_notifier_types() -> List[NotificationAdapter]:
    """Get a list of available notifier types."""
    try:
        return [NotificationAdapter(adapter.value) for adapter in NotificationAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/notifiers/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_notifier_config_schema(
    adapter_type: NotificationAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific notifier type."""
    try:
        try:
            notification_adapter = NotificationAdapter(adapter_type)
        except ValueError as e:
            raise ValueError(f"Invalid notification adapter type: {adapter_type}") from e

        # Get the corresponding configuration class for the adapter type
        notifier_config_type: Optional[type[NotificationConfig]] = config_service.get_notifier_config_by_type(
            notification_adapter
        )

        if notifier_config_type is None:
            raise NotifierConfigurationError(f"No configuration class found for adapter type {adapter_type}")

        # Map the configuration class to its corresponding schema
        notifier_config_schema = NOTIFICATION_CONFIG_SCHEMA_MAP.get(notifier_config_type, None)

        if notifier_config_schema is None:
            raise NotifierConfigurationError(f"No schema found for configuration class {notifier_config_type}")

        return notifier_config_schema.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/notifiers/{notifier_id}", response_model=NotifierSchema)
async def get_notifier_details(
    notifier_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> NotifierSchema:
    """Get details for a specific notifier."""
    try:
        notifier: Optional[Notifier] = config_service.get_notifier(notifier_id)

        if notifier is None:
            raise NotifierNotFoundError(f"Notifier with ID {notifier_id} not found")

        response = NotifierSchema.from_model(notifier)

        return response
    except NotifierNotFoundError as e:  # Catch specific domain errors if needed
        raise HTTPException(status_code=404, detail="Notifier not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/notifiers", response_model=NotifierSchema)
async def add_notifier(
    notifier_schema: NotifierCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> NotifierSchema:
    """Add a new notifier."""
    try:
        notifier_to_add: Notifier = notifier_schema.to_model()

        if notifier_to_add.config is None:
            raise NotifierConfigurationError("Notifier configuration should be set")

        new_notifier = config_service.add_notifier(
            name=notifier_to_add.name,
            adapter_type=notifier_to_add.adapter_type,
            config=notifier_to_add.config,
            external_service_id=notifier_to_add.external_service_id,
        )

        response = NotifierSchema.from_model(new_notifier)

        return response
    except NotifierAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NotifierConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/notifiers/{notifier_id}", response_model=NotifierSchema)
async def update_notifier(
    notifier_id: EntityId,
    notifier_update: NotifierUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> NotifierSchema:
    """Update a notifier's details."""
    try:
        notifier = config_service.get_notifier(notifier_id)

        if notifier is None:
            raise NotifierNotFoundError(f"Notifier with ID {notifier_id} not found")

        configuration: Optional[Configuration] = None
        if notifier_update.config:
            config_cls = config_service.get_notifier_config_by_type(notifier.adapter_type)
            if config_cls is None:
                raise NotifierConfigurationError(
                    f"No configuration class found for adapter type {notifier.adapter_type}"
                )
            configuration = config_cls.from_dict(notifier_update.config)

        external_service_id: Optional[EntityId] = None
        if notifier_update.external_service_id:
            external_service_id = EntityId(uuid.UUID(notifier_update.external_service_id))

        updated_notifier = config_service.update_notifier(
            notifier_id=notifier.id,
            name=notifier_update.name or "",
            config=cast(NotificationConfig, configuration),
            external_service_id=external_service_id,
        )

        response = NotifierSchema.from_model(updated_notifier)

        return response
    except NotifierNotFoundError as e:
        raise HTTPException(status_code=404, detail="Notifier not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/notifiers/{notifier_id}", response_model=NotifierSchema)
async def remove_notifier(
    notifier_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> NotifierSchema:
    """Remove a notifier."""
    try:
        deleted_notifier = config_service.remove_notifier(notifier_id)

        response = NotifierSchema.from_model(deleted_notifier)

        return response
    except NotifierNotFoundError as e:
        raise HTTPException(status_code=404, detail="Notifier not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/notifiers/{notifier_id}/test", response_model=Dict[str, str])
async def test_notifier(
    notifier_id: EntityId,
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> Dict[str, str]:
    """Test a notifier by sending a test notification."""
    try:
        notifier_port = adapter_service.get_notifier(notifier_id)

        if notifier_port is None:
            raise NotifierNotFoundError(f"Notifier with ID {notifier_id} not found")

        # Send a test notification
        test_title = "Test Notification"
        test_message = "This is a test notification from Edge Mining System"
        await notifier_port.send_notification(test_title, test_message)

        return {"status": "success", "message": "Test notification sent successfully"}
    except NotifierNotFoundError as e:
        raise HTTPException(status_code=404, detail="Notifier not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}") from e
