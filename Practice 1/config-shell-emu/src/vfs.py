"""Модуль виртуальной файловой системы (VFS)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


class VFSNode:
    """Узел виртуальной файловой системы: каталог или файл."""

    def __init__(
        self,
        name: str,
        is_dir: bool,
        parent: Optional["VFSNode"] = None,
    ) -> None:
        self.name = name
        self.is_dir = is_dir
        self.parent = parent
        self.children: dict[str, VFSNode] = {}
        self.content = ""


class VirtualFileSystem:
    """Хранит дерево VFS в оперативной памяти."""

    def __init__(self) -> None:
        self.root = VFSNode("/", True)
        self.cwd = self.root

    def load_from_xml(self, xml_path: str) -> None:
        """Загружает дерево VFS из XML без изменения исходного файла."""
        path = Path(xml_path)

        try:
            xml_tree = ET.parse(path)
        except FileNotFoundError as exc:
            raise ValueError(f"Файл VFS не найден: {xml_path}") from exc
        except ET.ParseError as exc:
            raise ValueError(f"Неверный формат XML: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Не удалось прочитать VFS: {exc}") from exc

        xml_root = xml_tree.getroot()
        if xml_root.tag != "vfs":
            raise ValueError("Корневой элемент XML должен называться <vfs>")

        new_root = VFSNode("/", True)
        self._parse_children(new_root, xml_root)
        self.root = new_root
        self.cwd = self.root

    def _parse_children(
        self,
        parent_node: VFSNode,
        xml_element: ET.Element,
    ) -> None:
        """Проверяет XML-узлы и добавляет их в дерево VFS."""
        for child in xml_element:
            if child.tag not in {"dir", "file"}:
                raise ValueError(
                    f"Недопустимый XML-элемент: <{child.tag}>"
                )

            name = child.attrib.get("name", "").strip()
            if not name:
                raise ValueError(
                    f"У элемента <{child.tag}> отсутствует атрибут name"
                )
            if name in {".", ".."} or "/" in name or "\\" in name:
                raise ValueError(f"Недопустимое имя файла или каталога: {name}")
            if name in parent_node.children:
                raise ValueError(f"Повторяющееся имя в каталоге: {name}")

            is_dir = child.tag == "dir"
            if not is_dir and len(child) > 0:
                raise ValueError(
                    f"Файл '{name}' не может содержать XML-элементы"
                )

            node = VFSNode(name, is_dir, parent_node)
            parent_node.children[name] = node

            if is_dir:
                self._parse_children(node, child)
            else:
                node.content = child.text or ""

    def get_node(self, path: str) -> Optional[VFSNode]:
        """Находит узел по абсолютному или относительному пути."""
        if not path or path == ".":
            return self.cwd

        if path.startswith("/"):
            current = self.root
        else:
            current = self.cwd

        parts = [part for part in path.split("/") if part]

        for part in parts:
            if part == ".":
                continue

            if not current.is_dir:
                return None

            if part == "..":
                if current.parent is not None:
                    current = current.parent
                continue

            current = current.children.get(part)
            if current is None:
                return None

        return current
