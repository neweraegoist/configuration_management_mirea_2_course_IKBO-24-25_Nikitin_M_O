
from __future__ import annotations

import xml.etree.ElementTree as element_tree
from pathlib import Path
from typing import Optional


class VFSNode:
    """Представляет файл или каталог в виртуальной файловой системе."""

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
    """Управляет виртуальными файлами и каталогами."""

    def __init__(self) -> None:
        self.root = VFSNode("/", True)
        self.cwd = self.root

    def load_from_xml(self, xml_path: str) -> None:
        """Загружает структуру виртуальной файловой системы из XML."""
        path = Path(xml_path)

        try:
            xml_tree = element_tree.parse(path)
        except FileNotFoundError as exc:
            raise ValueError(f"Файл VFS не найден: {xml_path}") from exc
        except element_tree.ParseError as exc:
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
        xml_element: element_tree.Element,
    ) -> None:
        """Разбирает дочерние элементы XML."""
        for child in xml_element:
            self._add_xml_child(parent_node, child)

    def _validate_xml_child(
        self,
        parent_node: VFSNode,
        child: element_tree.Element,
    ) -> tuple[str, bool]:
        """Проверяет XML-элемент и возвращает его имя и тип."""
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

        return name, is_dir

    def _add_xml_child(
        self,
        parent_node: VFSNode,
        child: element_tree.Element,
    ) -> None:
        """Создаёт узел и добавляет его в виртуальную файловую систему."""
        name, is_dir = self._validate_xml_child(parent_node, child)

        node = VFSNode(name, is_dir, parent_node)
        parent_node.children[name] = node

        if is_dir:
            self._parse_children(node, child)
        else:
            node.content = child.text or ""

    def get_node(self, path: str) -> Optional[VFSNode]:
        """Находит файл или каталог по указанному пути."""
        if not path or path == ".":
            return self.cwd

        current = self._start_node(path)
        parts = [part for part in path.split("/") if part]

        for part in parts:
            current = self._get_next_node(current, part)
            if current is None:
                return None

        return current

    def _start_node(self, path: str) -> VFSNode:
        """Выбирает начальный узел для поиска по пути."""
        if path.startswith("/"):
            return self.root
        return self.cwd

    def _get_next_node(
        self,
        current: VFSNode,
        part: str,
    ) -> Optional[VFSNode]:
        """Переходит к следующему элементу пути."""
        if part == ".":
            return current

        if not current.is_dir:
            return None

        if part == "..":
            if current.parent is not None:
                return current.parent
            return current

        return current.children.get(part)
