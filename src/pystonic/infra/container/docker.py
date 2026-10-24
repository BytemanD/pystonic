import dataclasses
from typing import Literal

import docker
import docker.errors
import requests.exceptions
import urllib3.exceptions
from docker.models import containers as docker_containers
from docker.models import images as docker_images
from docker.models import volumes as docker_volumes
from loguru import logger
from retry import retry

from pystonic.infra.container.exceptions import (
    ContainerNotExists,
    ContainerStatusNotMatch,
    CreateDockerClientFailed,
)


@dataclasses.dataclass
class Container:
    short_id: str
    name: str
    status: str
    image: str = ""
    command: list[str] = dataclasses.field(default_factory=list)
    autoRemove: bool | None = None

    def is_running(self) -> bool:
        return self.status in ["running", "active"]

    def to_json(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_raw_object(cls, container: docker_containers.Container):
        return Container(
            short_id=container.short_id,
            name=container.name or "",
            status=container.status or "",
            image=container.attrs.get("Config", {}).get("Image", ""),
            command=container.attrs.get("Config", {}).get("Cmd", []),
            autoRemove=container.attrs.get("HostConfig", {}).get("AutoRemove", []),
        )


@dataclasses.dataclass
class Image:
    short_id: str
    tags: list[str]
    size: int
    id: str | None = None

    @classmethod
    def from_raw_object(cls, image: docker_images.Image):
        return Image(
            short_id=image.short_id,
            id=image.id,
            tags=image.tags,
            size=image.attrs["Size"],
        )


@dataclasses.dataclass
class Volume:
    short_id: str
    name: str
    mountpoint: str = ""
    driver: str = ""
    created_at: str = ""
    labels: dict[str, str] | None = None

    @classmethod
    def from_raw_object(cls, volume: docker_volumes.Volume):
        return Volume(
            short_id=volume.short_id,
            name=volume.name,
            labels=volume.attrs.get("Labels") or {},
            driver=volume.attrs["Driver"],
            mountpoint=volume.attrs["Mountpoint"],
            created_at=volume.attrs["CreatedAt"],
        )


class DockerManager:
    def __init__(self) -> None:
        self._client = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            try:
                self._client = docker.from_env()
            except (
                docker.errors.DockerException,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.ProtocolError,
            ) as e:
                raise CreateDockerClientFailed(str(e))
        return self._client

    def system(self) -> dict:
        info = self.client.info()
        return {
            "version": info["ServerVersion"],
            "root_dir": info["DockerRootDir"],
            "driver": info["Driver"],
            "gpu_supported": bool(info.get("Runtimes", {}).get("nvidia")),
            "containers_running": info["ContainersRunning"],
            "containers_stopped": info["ContainersStopped"],
            "containers_paursed": info["ContainersPaused"],
            "images": info["Images"],
            "containers": info["Containers"],
        }

    def containers(self, all_status=False):
        containers = self.client.containers.list(all=all_status)
        return [Container.from_raw_object(container) for container in containers]

    def _get_container(self, id_or_name: str) -> docker_containers.Container:
        container = self.client.containers.get(id_or_name)
        if not container:
            raise ContainerNotExists(id_or_name)
        return container

    def get_container(self, id_or_name: str):
        return Container.from_raw_object(self._get_container(id_or_name))

    def run_container(
        self,
        image,
        name=None,
        command=None,
        auto_remove=False,
        detach: Literal[True] = True,
    ):
        self.client.containers.run(
            image=image,
            name=name,
            command=command,
            auto_remove=auto_remove,
            detach=detach,
        )

    def rm_container(self, id_or_name: str, force=False):
        container = self._get_container(id_or_name)
        container.remove(force=force)

    def start_container(self, id_or_name: str, wait=False) -> Container:
        container = self._get_container(id_or_name)
        logger.info("start container {}", id_or_name)
        container.start()
        if not wait:
            return Container.from_raw_object(container)
        return self._wait_container_status(id_or_name, ["running", "active"])

    def stop_container(self, id_or_name: str, timeout=None, wait=False) -> Container:
        container = self._get_container(id_or_name)
        logger.info("stop container {}", id_or_name)
        container.stop(timeout=timeout)
        if not wait:
            return Container.from_raw_object(container)
        return self._wait_container_status(id_or_name, ["exited", "stopped"])

    def pause_container(self, id_or_name: str):
        container = self._get_container(id_or_name)
        container.pause()

    def unpause_container(self, id_or_name: str):
        container = self._get_container(id_or_name)
        container.unpause()

    def resize_container(self, id_or_name: str, height: int, width: int):
        container = self._get_container(id_or_name)
        container.resize(height, width)

    def images(self, show_intermediate=False) -> list[Image]:
        images = self.client.images.list(all=show_intermediate)
        return [Image.from_raw_object(image) for image in images]

    def get_image(self, image_id) -> Image:
        image = self.client.images.get(image_id)
        return Image.from_raw_object(image)

    def remove_image(self, id_or_tag: str, force=False):
        logger.info("remove image {}", id_or_tag)
        self.client.images.remove(id_or_tag, force=force)

    def add_image_tag(
        self, image_id: str, repository: str, tag: str | None = None
    ) -> list[str]:
        logger.info("image {} add tag: {}:{}", image_id, repository, tag)
        image = self.client.images.get(image_id)
        image.tag(repository, tag or "latest")
        return image.tags

    def prune_images(self):
        self.client.images.prune()

    def volumes(self) -> list[Volume]:
        items = self.client.volumes.list()
        return [Volume.from_raw_object(volume) for volume in items]

    def get_volume(self, volume_id) -> Volume:
        volume = self.client.volumes.get(volume_id)
        return Volume.from_raw_object(volume)

    def create_volume(
        self, name=None, driver=None, label: dict[str, str] | None = None
    ) -> Volume:
        volume = self.client.volumes.create(name=name, driver=driver, label=label)
        return Volume.from_raw_object(volume)

    def rm_volume(self, volume_id, force=False):
        volume = self.client.volumes.get(volume_id)
        volume.remove(force=force)

    @retry(ContainerStatusNotMatch, tries=60, delay=1)
    def _wait_container_status(self, id_or_name, expect: list[str]) -> Container:
        new_container = self.get_container(id_or_name)
        logger.info("container {} status is {}", id_or_name, new_container.status)
        if new_container.status in expect:
            return new_container
        raise ContainerStatusNotMatch(id_or_name, new_container.status, expect)
