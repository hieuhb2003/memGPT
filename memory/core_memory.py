"""
Core Memory (Working Context) management.
This is a fixed-size read/write block containing key facts and current state.
"""
from typing import Dict, Optional


class CoreMemory:
    """
    Manages the Working Context - a structured memory block for key information.

    The Working Context contains multiple sections (e.g., 'persona', 'human')
    that can be read and modified via function calls.
    """

    def __init__(self, sections: Optional[Dict[str, str]] = None):
        """
        Initialize Core Memory with predefined sections.

        Args:
            sections: Dictionary of section names to initial content
        """
        if sections is None:
            sections = {
                'persona': 'I am MemGPT, an intelligent memory management system.',
                'human': 'No information about the user yet.',
            }
        self.sections = sections

    def get_section(self, section: str) -> Optional[str]:
        """
        Retrieve content from a specific section.

        Args:
            section: Name of the section to retrieve

        Returns:
            Content of the section, or None if not found
        """
        return self.sections.get(section)

    def append(self, section: str, content: str) -> bool:
        """
        Append content to a section.

        Args:
            section: Name of the section
            content: Content to append

        Returns:
            True if successful, False if section doesn't exist
        """
        if section not in self.sections:
            return False

        self.sections[section] += f"\n{content}"
        return True

    def replace(self, section: str, old_content: str, new_content: str) -> bool:
        """
        Replace specific content within a section.

        Args:
            section: Name of the section
            old_content: Content to be replaced
            new_content: New content

        Returns:
            True if successful, False if section doesn't exist or old_content not found
        """
        if section not in self.sections:
            return False

        current = self.sections[section]
        if old_content not in current:
            return False

        self.sections[section] = current.replace(old_content, new_content, 1)
        return True

    def to_string(self) -> str:
        """
        Convert Core Memory to a formatted string for inclusion in prompts.

        Returns:
            Formatted string representation of all sections
        """
        lines = ["### Core Memory (Working Context) ###"]
        for section, content in self.sections.items():
            lines.append(f"\n[{section.upper()}]")
            lines.append(content)
        lines.append("\n### End Core Memory ###\n")
        return "\n".join(lines)

    def get_all_sections(self) -> Dict[str, str]:
        """
        Get all sections as a dictionary.

        Returns:
            Dictionary of section names to content
        """
        return self.sections.copy()

    def create_section(self, section: str, initial_content: str = "") -> bool:
        """
        Create a new section.

        Args:
            section: Name of the new section
            initial_content: Initial content for the section

        Returns:
            True if created, False if section already exists
        """
        if section in self.sections:
            return False

        self.sections[section] = initial_content
        return True

    def delete_section(self, section: str) -> bool:
        """
        Delete a section.

        Args:
            section: Name of the section to delete

        Returns:
            True if deleted, False if section doesn't exist
        """
        if section not in self.sections:
            return False

        del self.sections[section]
        return True
