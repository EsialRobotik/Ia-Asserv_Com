import argparse
import json

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Placeholder, Button, Log, Input , Label, RadioButton, Rule 

from textual import content

import serial
import cbor2
from src.asserv_com_input import *
from src.asserv_com_output import *

def is_float(element: any) -> bool:
    #If you expect None to be passed:
    if element is None: 
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False

class Header(Placeholder):
    def set_text(self, text: str) -> None:
        """Met à jour le texte affiché dans le Header."""
        self._renderables["default"] = text
        self.refresh()

class Footer(Horizontal):
    pass

class ColumnsContainer(Horizontal):
    pass

class AsservUi(App):
    CSS = """
    Screen { align: center middle; }
    Header {
        height: 3;
        dock: top;
    }
    Footer {
        height: 3;
        dock: bottom;
    }
    Horizontal {
        height: auto;
        align: left top;
    }
    .columns-container {
        width: 1fr;
        height: 1fr;
        border: solid white;
    }
    .column1 {
        width: 55%;
        height: 100%;
    }
    .column2 {
        width: 45%;
        height: 100%;
    }
    .button {
        margin: 0 2;
        height: 3;
    }
    .logs {
        padding: 2;
        border: solid white;
    }
    .margin-top {
        margin-top: 1;
    }
    Static {
        width: 10;
        height: 3;
        content-align: center middle;
    }
    Input {
        width: 10;
        height: 3;
        text-align: center;
    }
    .currentId{
        width: 55%;
    }

    .orbitalStyle{
        width: 20%;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        # The uart line to read/write
        self.uart = serial.Serial('/dev/ttyACM0', 115200)
        # The state machine that decode the input stream
        self.stateMachine = InputCborStateMachine()

        self.queueNoStopMsg = []

        self.current_msg_id=0



    def compose(self) -> ComposeResult:
        yield Footer(
            Horizontal(
                Button("Quitter", id="quit", variant="error", classes="button"),
                Label("Cmd ID courante : 0", expand=True, classes="currentId", id="current_id"),
            ),
            id="footer"
        )
        yield Horizontal(
            Vertical(
                Header("Contrôle du robot"),
                Horizontal(
                    Button("Arrêt d'urgence", id="emergency_stop", variant="error", classes="button"),
                    Button("Reset arrêt d'urgence", id="reset_stop", variant="success", classes="button"),
                    Button("Low speed", id="low_speed", variant="warning", classes="button"),
                    Button("Normal speed", id="normal_speed", variant="success", classes="button"),
                    classes="margin-top",
                ),
                Rule(),
                Horizontal(
                    Horizontal(
                        Static("Go"),
                        Input(placeholder="Distance", id="go_dist"),
                        Button("Go", id="go", variant="primary", classes="button"),
                    ),
                    Horizontal(
                        Static("Turn"),
                        Input(placeholder="Degree", id="turn_degree"),
                        Button("Turn", id="turn", variant="primary", classes="button"),
                    ),
                    classes="margin-top",
                ),
                Horizontal(
                    Horizontal(
                        Static("GoTo"),
                        Input(placeholder="X", id="goto_x"),
                        Input(placeholder="Y", id="goto_y"),
                        Button("GoTo", id="goto", variant="primary", classes="button"),
                    ),
                    Horizontal(
                        Static("Face"),
                        Input(placeholder="X", id="face_x"),
                        Input(placeholder="Y", id="face_y"),
                        Button("Face", id="face", variant="primary", classes="button"),
                    ),
                    classes="margin-top",
                ),
                Rule(),
                Horizontal(
                    Static("Orbital Turn"),
                    Input(placeholder="Degree", id="orbital_angle", classes="orbitalStyle"),
                    RadioButton("Forward ?", value=True, classes="orbitalStyle", id="orbital_fw"),
                    RadioButton("To the right ?", value=True, classes="orbitalStyle", id="orbital_right"),
                    Button("Orbital turn", id="orbital", variant="primary", classes="button"),
                ),
                Rule(),
                Horizontal(
                        Static("GoToNoStop"),
                        Input(placeholder="X", id="gotonostop_x"),
                        Input(placeholder="Y", id="gotonostop_y"),
                        Button("Queue GoTo NoStop", id="gotonostop", variant="primary", classes="button"),
                    ),
                Horizontal(
                    Label(f"Nombre de commande NoStop en file: {len(self.queueNoStopMsg)}", expand=True, classes="currentId", id="nb_nostop_queued"),
                    Button("Send queued NoStop", id="nostopsend", variant="primary", classes="button"),
                ),
                
                classes="column1",
            ),
            Vertical(
                Header("Logs"),
                Log(classes="logs", id="logs"),
                classes="column2",
            ),
            classes="columns-container",
        )

    def on_ready(self) -> None:
        self.update_position()
        self.set_interval(0.001, self.update_position)

    def update_position(self) -> None:
        log = self.query_one("#logs")
        x = self.uart.read() 
        for val in x :
            self.stateMachine.push_byte(val)

        if self.stateMachine.get_nb_payload() > 0 :
            payload = self.stateMachine.pop_payload()
            log.write_line(f"X:{payload['X']} Y:{payload['Y']} \u03B8:{payload['Theta']:.3f} / cmd Id:{payload['cmd_id']} status:{payload['status']} nb pending:{payload['pending']} / Motor left:{payload['motor_left']} Motor right:{payload['motor_right']}")





    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'quit':
            self.exit()
        elif event.button.id == 'emergency_stop':
            stop_msg = createEmergencyStopMessage()
            self.uart.write(stop_msg)
        elif event.button.id == 'reset_stop':
            stop_rst_msg = createEmergencyStopResetMessage()
            self.uart.write(stop_rst_msg)
        elif event.button.id == 'low_speed':
            low_speed_msg = createSlowAccSpeedModeMessage()
            self.uart.write(low_speed_msg)
        elif event.button.id == 'normal_speed':
            low_speed_msg = createNormalAccSpeedModeMessage()
            self.uart.write(low_speed_msg)
        elif event.button.id == 'go':
            dist = self.query_one("#go_dist").value
            if( is_float(dist)) :
                go_msg = createStraightMessage(self.current_msg_id, float(dist))
                self.uart.write(go_msg)
                self.current_msg_id+=1
            else:
                self.notify("Une distance pour le Go non ?", severity="error", timeout=5)
        elif event.button.id == 'turn':
            angle = self.query_one("#turn_degree").value
            if( is_float(angle)) :
                turn_msg = createTurnMessage(self.current_msg_id, float(angle))
                self.uart.write(turn_msg)         
                self.current_msg_id+=1
            else:
                self.notify("Et l'angle ?", severity="error", timeout=5)                
        elif event.button.id == 'goto':
            x = self.query_one("#goto_x").value
            y = self.query_one("#goto_y").value
            if( is_float(x) and is_float(y)) :
                goto_msg = createGotoMessage(self.current_msg_id, float(x), float(y))
                self.uart.write(goto_msg)         
                self.current_msg_id+=1
            else:
                self.notify("Ton point de consigne c'est dla merde!", severity="error", timeout=5)                                
        elif event.button.id == 'face':
            x = self.query_one("#face_x").value
            y = self.query_one("#face_y").value
            if( is_float(x) and is_float(y)) :
                face_msg = createFaceMessage(self.current_msg_id, float(x), float(y))
                self.uart.write(face_msg)         
                self.current_msg_id+=1
            else:
                self.notify("Face de con !", severity="error", timeout=5)      
        elif event.button.id == 'orbital':
            angle = self.query_one("#orbital_angle").value
            fw = self.query_one("#orbital_fw").value
            right = self.query_one("#orbital_right").value

            if( is_float(angle)) :
                orbital_msg = createOrbitalTurnMessage(self.current_msg_id, float(angle), fw, right)
                self.uart.write(orbital_msg)         
                self.current_msg_id+=1
            else:
                self.notify("Et l'angle je l'invente?", severity="error", timeout=5)      

        elif event.button.id == 'gotonostop':
            x = self.query_one("#gotonostop_x").value
            y = self.query_one("#gotonostop_y").value
            if( is_float(x) and is_float(y)) :
                gotoNostop_msg = createGotoNoStopMessage(self.current_msg_id, float(x), float(y))
                self.queueNoStopMsg.append(gotoNostop_msg)
                self.query_one("#nb_nostop_queued").update(f"Nombre de commande NoStop en file: {len(self.queueNoStopMsg)}")
                self.current_msg_id+=1
            else:
                self.notify("Ton X/Y nostop c'est dla marde!", severity="error", timeout=5)     

        elif event.button.id == 'nostopsend':
            for msg in self.queueNoStopMsg :
                self.uart.write(msg)         

            self.queueNoStopMsg = []
            self.query_one("#nb_nostop_queued").update(f"Nombre de commande NoStop en file: {len(self.queueNoStopMsg)}")


        self.query_one("#current_id").update(f"Cmd ID courante : {self.current_msg_id}")

            




if __name__ == "__main__":
    app = AsservUi()
    app.run()