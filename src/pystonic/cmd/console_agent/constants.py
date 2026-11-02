APP_CSS = """
Screen {
    layout: horizontal;
}

VerticalScroll {
    scrollbar-size: 1 1;
}
#sidebar {
    width: 24;
    border-right: solid $primary;
}


#session-list {
    height: 1fr;
    border: none;
    padding: 0 1;
    scrollbar-size: 1 1;
}

#main-panel {
    width: 1fr;
    layout: vertical;
}

#chat-view {
    height: 1fr;
    padding: 1 2;
}

.user-msg {
    background: $primary 15%;
    border-left: thick $primary;
}

.ai-msg-reasoning {
    background: grey 10%;
    margin: 1 6 1 4;
}

.ai-msg {
    background: $surface 10%;
    margin: 1 6 1 0;
    padding: 0 2;
}

#input-bar {
    height: auto;
    dock: bottom;
    padding: 1 2;
    background: $surface;
}

#chat-input {
    border: tall $primary;
}

#session-context-menu {
    position: absolute;
    width: 16;
    height: auto;
    padding: 1;
    background: $surface;
    border: solid $primary;
}

#session-context-menu Button {
    width: 100%;
    margin: 0;
}
"""
