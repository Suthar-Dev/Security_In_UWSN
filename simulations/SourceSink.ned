//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

package billo.simulations;

import billo.Source;
import billo.Sink;
import billo.Txc2;

//
// Sample network, consisting of a source and a sink.
//
network SourceSink
{
    @display("bgb=451,298");
    submodules:

        service_station: Sink {
            @display("p=238,153;i=device/antennatower");
        }
        sensor1: Source {
            @display("p=86,251;i=misc/sensor");
        }
        sensor2: Source {
            @display("p=181,251;i=misc/sensor");
        }
        sensor3: Source {
            @display("p=277,251;i=misc/sensor");
        }
        sensor4: Source {
            @display("p=374,251;i=misc/sensor");
        }
        offshore_station: Txc2 {
            @display("p=238,48;i=old/pctower2");
        }

    connections:
        sensor1.out --> service_station.in1;
        sensor2.out --> service_station.in2;
        sensor3.out --> service_station.in3;
        sensor4.out --> service_station.in4;
        service_station.out <--> offshore_station.port;



}
