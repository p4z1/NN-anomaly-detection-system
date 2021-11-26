import csv
import os
from collections import defaultdict

import requests
from scapy.sessions import DefaultSession

from .features.context.packet_direction import PacketDirection
from .features.context.packet_flow_key import get_packet_flow_key
from .flow import Flow

EXPIRED_UPDATE = 40
MACHINE_LEARNING_API = "http://localhost:8000/predict"


class FlowSession(DefaultSession):
    """Creates a list of network flows."""

    def __init__(self, *args, **kwargs):
        self.flows = {}
        self.csv_line = 0
        self.flowID = 0
        self.csvDir = "./csvFiles/"
        if self.output_mode == "flow":
            if not os.path.exists(self.csvDir):
                os.mkdir(self.csvDir)
            #output = open(self.output_file, "w")
            #self.csv_writer = csv.writer(output)

        self.packets_count = 0

        self.clumped_flows_per_label = defaultdict(list)

        super(FlowSession, self).__init__(*args, **kwargs)

    def toPacketList(self):
        # Sniffer finished all the packets it needed to sniff.
        # It is not a good place for this, we need to somehow define a finish signal for AsyncSniffer
        self.garbage_collect(None)
        return super(FlowSession, self).toPacketList()

    def on_packet_received(self, packet):
        count = 0
        direction = PacketDirection.FORWARD

        if self.output_mode != "flow":
            if "IP" not in packet:
                return

        self.packets_count += 1

        # Creates a key variable to check
        packet_flow_key = get_packet_flow_key(packet, direction)
        flow = self.flows.get((packet_flow_key, count))

        # If there is no forward flow with a count of 0
        if flow is None:
            # There might be one of it in reverse
            direction = PacketDirection.REVERSE
            packet_flow_key = get_packet_flow_key(packet, direction)
            flow = self.flows.get((packet_flow_key, count))

            if flow is None:
                # If no flow exists create a new flow
                direction = PacketDirection.FORWARD
                flow = Flow(packet, direction)
                packet_flow_key = get_packet_flow_key(packet, direction)
                self.flows[(packet_flow_key, count)] = flow

            elif (packet.time - flow.latest_timestamp) > EXPIRED_UPDATE:
                # If the packet exists in the flow but the packet is sent
                # after too much of a delay than it is a part of a new flow.
                expired = EXPIRED_UPDATE
                while (packet.time - flow.latest_timestamp) > expired:
                    count += 1
                    expired += EXPIRED_UPDATE
                    flow = self.flows.get((packet_flow_key, count))

                    if flow is None:
                        flow = Flow(packet, direction)
                        self.flows[(packet_flow_key, count)] = flow
                        break

        elif (packet.time - flow.latest_timestamp) > EXPIRED_UPDATE:
            expired = EXPIRED_UPDATE
            while (packet.time - flow.latest_timestamp) > expired:

                count += 1
                expired += EXPIRED_UPDATE
                flow = self.flows.get((packet_flow_key, count))

                if flow is None:
                    flow = Flow(packet, direction)
                    self.flows[(packet_flow_key, count)] = flow
                    break

        flow.add_packet(packet, direction)

        if self.packets_count % 100 == 0 or (
            flow.duration > 120 and self.output_mode == "flow"
        ):
            print("Packet count: {}".format(self.packets_count))
            self.garbage_collect(packet.time)

    def get_flows(self) -> list:
        return self.flows.values()

    def garbage_collect(self, latest_time) -> None:
        # TODO: Garbage Collection / Feature Extraction should have a separate thread
        print("Garbage Collection Began. Flows = {}".format(len(self.flows)))
        output = open(self.csvDir+str(self.flowID)+".csv", "w")
        csv_writer = csv.writer(output)
        keys = list(self.flows.keys())
        self.csv_line = 0
        if len(self.flows) > 784:
            for k in keys:
                if self.csv_line >= 784:
                    break
                flow = self.flows.get(k)

                data = flow.get_data()
                # POST Request to Model API

                if self.csv_line == 0:
                    csv_writer.writerow(data.keys())
                csv_writer.writerow(data.values())
                self.csv_line += 1
                del self.flows[k]
                
            self.flowID += 1
            self.csv_line = 0
            output.close()

        print("Garbage Collection Finished. Flows = {}".format(len(self.flows)))

def generate_session_class(output_mode, output_file, url_model):
    return type(
        "NewFlowSession",
        (FlowSession,),
        {
            "output_mode": output_mode,
            "output_file": output_file,
            "url_model": url_model,
        },
    )
