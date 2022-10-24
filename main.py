import json
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.trace import ReadableSpan
from time import time_ns

json_parse_acc_attribute = 'com.aspecto.json_parse_duration_ns'

provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

class MySpanProcessor(BatchSpanProcessor):
    def on_end(self, span: ReadableSpan) -> None:
        super().on_end(span)
        json_parse_acc = span.attributes.get(json_parse_acc_attribute)
        if json_parse_acc:
            virtual_span = tracer.start_span('json_parse', context=trace.set_span_in_context(span), start_time=span.start_time)
            end_time = span.start_time + json_parse_acc
            virtual_span.end(end_time=end_time)

processor = MySpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)

def instrumented_parse_json(json_string):
    current_span = trace.get_current_span()
    acc_json_parse_duration = current_span.attributes.get(json_parse_acc_attribute, 0)

    json_parse_start = time_ns()
    json.loads(json_string)
    json_parse_end = time_ns()
    json_parse_duration = json_parse_end - json_parse_start
    print(f"json parse duration: {json_parse_duration}")
    acc_json_parse_duration += json_parse_duration
    current_span.set_attribute(json_parse_acc_attribute, acc_json_parse_duration)

with tracer.start_as_current_span("foo") as parent:
    instrumented_parse_json('{"foo": "bar"}')
    #big json
    instrumented_parse_json('''{
  "colors": [
    {
      "color": "black",
      "category": "hue",
      "type": "primary",
      "code": {
        "rgba": [255,255,255,1],
        "hex": "#000"
      }
    },
    {
      "color": "white",
      "category": "value",
      "code": {
        "rgba": [0,0,0,1],
        "hex": "#FFF"
      }
    },
    {
      "color": "red",
      "category": "hue",
      "type": "primary",
      "code": {
        "rgba": [255,0,0,1],
        "hex": "#FF0"
      }
    },
    {
      "color": "blue",
      "category": "hue",
      "type": "primary",
      "code": {
        "rgba": [0,0,255,1],
        "hex": "#00F"
      }
    },
    {
      "color": "yellow",
      "category": "hue",
      "type": "primary",
      "code": {
        "rgba": [255,255,0,1],
        "hex": "#FF0"
      }
    },
    {
      "color": "green",
      "category": "hue",
      "type": "secondary",
      "code": {
        "rgba": [0,255,0,1],
        "hex": "#0F0"
      }
    }
  ]
}''')
