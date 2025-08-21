from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane, Input, RichLog
from textual.binding import Binding
from textual import on
from rich.text import Text

from ..models import Message, AgentState


class AgentTab(TabPane):
    def __init__(self, agent_name: str, *args, **kwargs):
        super().__init__(agent_name, *args, **kwargs)
        self.agent_state = AgentState(
            name=agent_name,
            system_prompt="You are a helpful coding and ops agent."
        )

    def compose(self) -> ComposeResult:
        with Vertical():
            yield RichLog(id="message_log", highlight=True, markup=True)
            yield Input(placeholder="Enter your prompt...", id="prompt_input")

    def add_message(self, message: Message) -> None:
        log = self.query_one("#message_log", RichLog)
        
        if message.role == "user":
            log.write(Text(f"[bold blue]User:[/bold blue] {message.content}"))
        elif message.role == "assistant":
            log.write(Text(f"[bold green]Assistant:[/bold green] {message.content}"))
        elif message.role == "tool":
            log.write(Text(f"[bold yellow]Tool:[/bold yellow] {message.content}"))
        elif message.role == "error":
            log.write(Text(f"[bold red]Error:[/bold red] {message.content}"))
        
        self.agent_state.history.append(message)


class RyAgentApp(App):
    TITLE = "RyAgent"
    CSS_PATH = "styles.css"
    
    BINDINGS = [
        Binding("ctrl+tab", "next_tab", "Next Tab"),
        Binding("ctrl+shift+tab", "prev_tab", "Previous Tab"),
        Binding("t", "new_tab", "New Tab"),
        Binding("x", "close_tab", "Close Tab"),
        Binding("ctrl+c", "interrupt", "Interrupt"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.tab_counter = 1

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_container"):
            with TabbedContent(id="tabs"):
                yield AgentTab("Agent 1", id="tab-1")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "RyAgent - Your personal multi-agent operator"

    @on(Input.Submitted)
    def handle_prompt_submission(self, event: Input.Submitted) -> None:
        if event.input.id == "prompt_input":
            prompt = event.value.strip()
            if prompt:
                tabs = self.query_one("#tabs", TabbedContent)
                active_tab = tabs.active_pane
                if isinstance(active_tab, AgentTab):
                    user_message = Message(role="user", content=prompt)
                    active_tab.add_message(user_message)
                    event.input.value = ""
                    
                    reply_message = Message(
                        role="assistant", 
                        content=f"Echo: {prompt} (LLM integration coming soon)"
                    )
                    active_tab.add_message(reply_message)

    def action_new_tab(self) -> None:
        self.tab_counter += 1
        tabs = self.query_one("#tabs", TabbedContent)
        new_tab = AgentTab(f"Agent {self.tab_counter}", id=f"tab-{self.tab_counter}")
        tabs.add_pane(new_tab)
        tabs.active = f"tab-{self.tab_counter}"

    def action_close_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        if len(tabs.tabs) > 1:
            tabs.remove_pane(tabs.active)

    def action_next_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_names = [tab.id for tab in tabs.tabs]
        current_index = tab_names.index(tabs.active)
        next_index = (current_index + 1) % len(tab_names)
        tabs.active = tab_names[next_index]

    def action_prev_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_names = [tab.id for tab in tabs.tabs]
        current_index = tab_names.index(tabs.active)
        prev_index = (current_index - 1) % len(tab_names)
        tabs.active = tab_names[prev_index]

    def action_interrupt(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        active_tab = tabs.active_pane
        if isinstance(active_tab, AgentTab):
            if active_tab.agent_state.running:
                error_message = Message(role="error", content="Task interrupted by user")
                active_tab.add_message(error_message)
                active_tab.agent_state.running = False
                active_tab.agent_state.current_task_id = None