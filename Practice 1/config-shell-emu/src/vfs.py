"""Модуль виртуальной файловой системы (VFS)."""
from __future__ import annotations
import xml.etree.ElementTree as ET

class VFSNode:
    """Узел файловой системы (папка или файл)."""
    def __init__(self, name: str, is_dir: bool, parent: 'VFSNode | None' = None):
        self.name = name
        self.is_dir = is_dir
        self.parent = parent
        self.children: dict[str, VFSNode] = {}
        self.content = ""

class VirtualFileSystem:
    """Виртуальная файловая система в памяти."""
    def __init__(self):
        self.root = VFSNode("/", True)
        self.cwd = self.root # Текущая директория (Current Working Directory)

    def load_from_xml(self, xml_path: str) -> None:
        """Загружает VFS из XML-файла."""
        try:
            tree = ET.parse(xml_path)
            root_elem = tree.getroot()
            self.root = VFSNode("/", True)
            self._parse_children(self.root, root_elem)
            self.cwd = self.root
        except FileNotFoundError:
            raise ValueError(f"Файл VFS не найден: {xml_path}")
        except ET.ParseError as exc:
            raise ValueError(f"Неверный формат XML: {exc}")

    def _parse_children(self, parent_node: VFSNode, xml_elem: ET.Element) -> None:
        """Рекурсивно обходит XML и строит дерево."""
        for child in xml_elem:
            is_dir = (child.tag == "dir")
            node = VFSNode(child.attrib.get("name", "unknown"), is_dir, parent_node)
            if not is_dir:
                node.content = child.text or ""
            parent_node.children[node.name] = node
            if is_dir:
                self._parse_children(node, child)

    def get_node(self, path: str) -> 'VFSNode | None':
        """Возвращает узел по указанному пути (относительно cwd или абсолютному)."""
        if not path or path == ".":
            return self.cwd
        
        # Разбираемся с абсолютным и относительным путями
        if path.startswith("/"):
            current = self.root
            parts = [p for p in path.split("/") if p]
        else:
            current = self.cwd
            parts = [p for p in path.split("/") if p]

        for part in parts:
            if part == ".":
                continue
            if part == "..":
                if current.parent:
                    current = current.parent
                continue
            
            if not current.is_dir or part not in current.children:
                return None # Путь не найден
            current = current.children[part]
            
        return current
  
