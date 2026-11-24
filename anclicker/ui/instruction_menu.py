"""Shared instruction categories for table and graph insertion menus."""
from anclicker.ui.context_menu_style import style_context_menu


def add_instruction_categories(menu, specs, owner):
    actions, categories, submenus = {}, {}, []
    for type_id, spec in specs.items():
        categories.setdefault(spec.category, []).append((type_id, spec.title))
    for category, entries in categories.items():
        submenu = menu.addMenu(category)
        submenus.append(submenu)
        style_context_menu(submenu, owner)
        for type_id, title in entries:
            actions[submenu.addAction(title)] = type_id
    menu._instruction_submenus = submenus
    return actions
