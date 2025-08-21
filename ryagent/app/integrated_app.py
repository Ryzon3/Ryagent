import asyncio
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane, Input, RichLog
from textual.binding import Binding
from textual import on
from rich.text import Text

from ..models import Message, AgentState
from ..llm.client import LLMClient
from ..tools.base import ToolRegistry
from ..tools.core_tools import ShellRunTool, FileReadTool, FileWriteTool
from ..agents.base_agent import BaseAgent
from ..runtime.events import EventBus, EventType, ErrorEvent


class AgentTab(TabPane):
    def __init__(self, agent_name: str, *args, **kwargs):
        super().__init__(agent_name, *args, **kwargs)
        self.agent_state = AgentState(
            name=agent_name,
            system_prompt="You are a helpful coding and ops agent."
        )
        self.agent: BaseAgent | None = None
        self.event_bus: EventBus | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield RichLog(id="message_log", highlight=True, markup=True)
            yield Input(placeholder="Enter your prompt...", id="prompt_input")

    def setup_agent(self, llm_client: LLMClient, tool_registry: ToolRegistry, event_bus: EventBus):
        self.event_bus = event_bus
        self.agent = BaseAgent(
            agent_state=self.agent_state,
            llm_client=llm_client,
            tool_registry=tool_registry,
            event_bus=event_bus
        )

    def add_message(self, message: Message) -> None:
        log = self.query_one("#message_log", RichLog)
        
        if message.role == "user":
            log.write(Text(f"[bold blue]User:[/bold blue] {message.content}"))
        elif message.role == "assistant":
            if "tool_calls" in message.meta:
                log.write(Text(f"[bold green]Assistant:[/bold green] {message.content or '(requesting tools)'}"))
                for tool_call in message.meta["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    log.write(Text(f"[yellow]→ Calling tool: {tool_name}[/yellow]"))
            else:
                log.write(Text(f"[bold green]Assistant:[/bold green] {message.content}"))
        elif message.role == "tool":
            log.write(Text(f"[bold yellow]Tool Result:[/bold yellow] {message.content[:200]}{'...' if len(message.content) > 200 else ''}"))
        elif message.role == "error":
            log.write(Text(f"[bold red]Error:[/bold red] {message.content}"))

    async def send_prompt(self, prompt: str) -> None:
        if self.agent and not self.agent_state.running:
            user_message = Message(role="user", content=prompt)
            self.add_message(user_message)
            
            task = self.agent.start_task(
                self.agent.process_prompt(prompt, self.id)
            )
            
            try:
                await task
            except asyncio.CancelledError:
                error_msg = Message(role="error", content="Task was interrupted")
                self.add_message(error_msg)

    async def interrupt_agent(self) -> None:
        if self.agent and self.agent_state.running:
            await self.agent.interrupt()
            error_msg = Message(role="error", content="Task interrupted by user")
            self.add_message(error_msg)


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
        self.event_bus = EventBus()
        self.llm_client = None
        self.tool_registry = ToolRegistry()
        self._setup_tools()
        self._event_processor_task: asyncio.Task | None = None

    def _setup_tools(self):
        workspace = os.getcwd()
        
        shell_tool = ShellRunTool(workspace=workspace)
        fs_read_tool = FileReadTool(workspace=workspace)
        fs_write_tool = FileWriteTool(workspace=workspace)
        
        self.tool_registry.register(shell_tool)
        self.tool_registry.register(fs_read_tool)
        self.tool_registry.register(fs_write_tool)
        
        self.tool_registry.authorize_tool("shell_run")
        self.tool_registry.authorize_tool("fs_read")
        self.tool_registry.authorize_tool("fs_write")

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_container"):
            with TabbedContent(id="tabs"):
                yield AgentTab("Agent 1", id="tab-1")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "RyAgent - Your personal multi-agent operator"
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm_client = LLMClient(api_key=api_key)
            
            tabs = self.query_one("#tabs", TabbedContent)
            for pane in tabs.query(AgentTab):
                pane.setup_agent(self.llm_client, self.tool_registry, self.event_bus)
        else:
            self._show_error("OPENAI_API_KEY environment variable not set")

        self._event_processor_task = asyncio.create_task(self._process_events())

    async def _process_events(self):
        event_queue = asyncio.Queue()
        self.event_bus.subscribe(EventType.AGENT_REPLY, event_queue)
        self.event_bus.subscribe(EventType.TOOL_RESULT, event_queue)
        self.event_bus.subscribe(EventType.ERROR, event_queue)

        while True:
            try:
                event = await event_queue.get()
                tab_id = event.tab_id
                
                tabs = self.query_one("#tabs", TabbedContent)
                target_tab = None
                for tab in tabs.tabs:
                    if tab.id == tab_id:
                        target_tab = tab
                        break

                if not isinstance(target_tab, AgentTab):
                    continue

                if event.type == EventType.AGENT_REPLY:
                    message = event.data["message"]
                    target_tab.add_message(message)
                elif event.type == EventType.TOOL_RESULT:
                    pass  # Tool results are already handled in agent
                elif event.type == EventType.ERROR:
                    error_msg = Message(role="error", content=event.data["error"])
                    target_tab.add_message(error_msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                pass

    def _show_error(self, message: str):
        tabs = self.query_one("#tabs", TabbedContent)
        active_tab = tabs.active_pane
        if isinstance(active_tab, AgentTab):
            error_msg = Message(role="error", content=message)
            active_tab.add_message(error_msg)

    @on(Input.Submitted)
    def handle_prompt_submission(self, event: Input.Submitted) -> None:
        if event.input.id == "prompt_input":
            prompt = event.value.strip()
            if prompt:
                tabs = self.query_one("#tabs", TabbedContent)
                active_tab = tabs.active_pane
                if isinstance(active_tab, AgentTab):
                    if not self.llm_client:
                        self._show_error("LLM client not initialized. Check OPENAI_API_KEY.")
                        return
                    
                    event.input.value = ""
                    asyncio.create_task(active_tab.send_prompt(prompt))

    def action_new_tab(self) -> None:
        self.tab_counter += 1
        tabs = self.query_one("#tabs", TabbedContent)
        new_tab = AgentTab(f"Agent {self.tab_counter}", id=f"tab-{self.tab_counter}")
        
        if self.llm_client:
            new_tab.setup_agent(self.llm_client, self.tool_registry, self.event_bus)
        
        tabs.add_pane(new_tab)
        tabs.active = f"tab-{self.tab_counter}"

    def action_close_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        if len(tabs.tabs) > 1:
            active_tab = tabs.active_pane
            if isinstance(active_tab, AgentTab):
                asyncio.create_task(active_tab.interrupt_agent())
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
            asyncio.create_task(active_tab.interrupt_agent())

    async def on_unmount(self) -> None:
        if self._event_processor_task:
            self._event_processor_task.cancel()
            try:
                await self._event_processor_task
            except asyncio.CancelledError:
                pass