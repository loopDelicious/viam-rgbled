import asyncio
from typing import ClassVar, Final, Mapping, Sequence, cast

from typing_extensions import Self
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily

from viam.components.board import Board
from viam.services.generic import Generic
from viam.logging import getLogger

LOGGER = getLogger(__name__)

class RgbLed(Generic, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("joyce", "generic"), "rgb_led")

    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> "RgbLed":
        instance = cls(config.name)
        instance.reconfigure(config, dependencies)
        return instance

    @classmethod
    def validate(cls, config: ComponentConfig):
        """Validate the configuration."""
        required_keys = {"board", "red_pin", "green_pin", "blue_pin"}
        missing_keys = [key for key in required_keys if key not in config.attributes]
        if missing_keys:
            raise ValueError(f"Missing configuration keys: {missing_keys}")
        return

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        """Reconfigure the component with updated configuration."""
        LOGGER.info("Reconfiguring RgbLed with new settings")

        board_name = config.attributes["board"]
        red_pin_name = config.attributes["red_pin"]
        green_pin_name = config.attributes["green_pin"]
        blue_pin_name = config.attributes["blue_pin"]

        self.board = cast(Board, dependencies[ResourceName.from_string(board_name)])
        self.red_pin = asyncio.run(self.board.gpio_pin_by_name(name=red_pin_name))
        self.green_pin = asyncio.run(self.board.gpio_pin_by_name(name=green_pin_name))
        self.blue_pin = asyncio.run(self.board.gpio_pin_by_name(name=blue_pin_name))

        LOGGER.info("RgbLed reconfiguration complete")

    async def set_color(self, red: int, green: int, blue: int):
        """Set the color of the RGB LED using PWM.

        Args:
            red (int): Brightness of the red component (0-100)
            green (int): Brightness of the green component (0-100)
            blue (int): Brightness of the blue component (0-100)
        """
        LOGGER.info(f"Setting RGB color to R: {red}, G: {green}, B: {blue}")
        await self.red_pin.set_pwm(red / 100.0)
        await self.green_pin.set_pwm(green / 100.0)
        await self.blue_pin.set_pwm(blue / 100.0)

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())