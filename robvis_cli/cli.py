"""
Command Line Interface for robvis-cli.
"""

import argparse
import sys
import os
from .models import ToolType
from .parser import parse_rob_csv
from .renderer_svg import render_traffic_light_svg, render_summary_bar_svg


SAMPLE_ROB2_CSV = """Study,D1,D2,D3,D4,D5,Overall,Weight
Al-Mansoor et al. 2021,Low,Low,Low,Low,Low,Low,120
Belikov et al. 2020,Some concerns,Low,Low,Low,Some concerns,Some concerns,85
Chen & Tanaka 2022,Low,Low,Low,Low,Low,Low,210
Dupont & Laurent 2019,High,Low,Low,Some concerns,Low,High,64
Espinosa et al. 2023,Low,Some concerns,Low,Low,Low,Some concerns,150
Farrokhzad et al. 2020,Low,Low,High,Low,Low,High,95
Gomez-Perez 2021,Low,Low,Low,Low,Low,Low,180
Hofmann et al. 2022,Some concerns,Some concerns,Low,Low,Low,Some concerns,110
Ibrahim & Khan 2023,Low,Low,Low,Some concerns,Low,Some concerns,140
Jensen et al. 2018,High,High,Low,Low,High,High,75
"""

SAMPLE_ROBINS_I_CSV = """Study,D1,D2,D3,D4,D5,D6,D7,Overall,Weight
Armstrong 2021,Moderate,Low,Low,Moderate,Low,Low,Low,Moderate,320
Bautista 2020,Serious,Moderate,Low,Low,Low,Moderate,Low,Serious,190
Carvalho 2022,Low,Low,Low,Low,Low,Low,Low,Low,450
Davenport 2019,Critical,Serious,Moderate,Low,Serious,Low,Low,Critical,115
Eberhardt 2023,Moderate,Low,Low,Low,Low,Low,Low,Moderate,280
"""


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="robvis",
        description="Publication-ready Cochrane Risk of Bias visualizer (RoB 2, ROBINS-I, QUADAS-2) — pure SVG.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: traffic-light
    tl_parser = subparsers.add_parser("traffic-light", help="Generate Traffic Light Matrix SVG")
    tl_parser.add_argument("-i", "--input", required=True, help="Path to Risk of Bias CSV file")
    tl_parser.add_argument("-o", "--output", default="traffic_light.svg", help="Output file path (.svg)")
    tl_parser.add_argument("-t", "--title", default="Risk of Bias Assessment", help="Chart title")
    tl_parser.add_argument("--tool", choices=["ROB2", "ROBINS_I", "QUADAS_2", "CUSTOM"], default=None, help="Force tool type")
    tl_parser.add_argument("--no-symbols", action="store_true", help="Hide +/-/? symbols inside circles")
    tl_parser.add_argument("--no-tooltips", action="store_true", help="Omit hover tooltips")

    # Subcommand: summary
    sum_parser = subparsers.add_parser("summary", help="Generate Domain Summary Bar Chart SVG")
    sum_parser.add_argument("-i", "--input", required=True, help="Path to Risk of Bias CSV file")
    sum_parser.add_argument("-o", "--output", default="summary_bar.svg", help="Output file path (.svg)")
    sum_parser.add_argument("-t", "--title", default="Risk of Bias Summary by Domain", help="Chart title")
    sum_parser.add_argument("--tool", choices=["ROB2", "ROBINS_I", "QUADAS_2", "CUSTOM"], default=None, help="Force tool type")
    sum_parser.add_argument("-w", "--weighted", action="store_true", help="Weight bars by study sample size / weight column")

    # Subcommand: validate
    val_parser = subparsers.add_parser("validate", help="Validate a Risk of Bias CSV dataset")
    val_parser.add_argument("-i", "--input", required=True, help="Path to Risk of Bias CSV file")

    # Subcommand: sample-csv
    sample_parser = subparsers.add_parser("sample-csv", help="Generate sample CSV dataset")
    sample_parser.add_argument("--tool", choices=["rob2", "robins-i"], default="rob2", help="Tool type sample")
    sample_parser.add_argument("-o", "--output", default=None, help="Save to file (prints to stdout if omitted)")

    args = parser.parse_args(argv)

    if args.command == "sample-csv":
        sample_text = SAMPLE_ROB2_CSV if args.tool == "rob2" else SAMPLE_ROBINS_I_CSV
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(sample_text)
            print(f"Sample {args.tool.upper()} CSV written to: {args.output}")
        else:
            sys.stdout.write(sample_text)
        return 0

    tool_enum = ToolType[args.tool] if hasattr(args, "tool") and args.tool else None

    if args.command == "validate":
        try:
            meta = parse_rob_csv(args.input, tool_type=tool_enum)
            print(f"Validation SUCCESS for: {args.input}")
            print(f"  Tool Detected: {meta.tool_type.value}")
            print(f"  Studies: {len(meta.assessments)}")
            print(f"  Domains: {len(meta.domains)} ({', '.join(meta.domain_keys())})")
            
            high_count = sum(1 for a in meta.assessments if a.overall.name in ("HIGH", "CRITICAL"))
            low_count = sum(1 for a in meta.assessments if a.overall.name == "LOW")
            some_count = sum(1 for a in meta.assessments if a.overall.name == "SOME_CONCERNS")
            print(f"  Overall Distribution: Low={low_count}, Some concerns={some_count}, High/Critical={high_count}")
            return 0
        except Exception as e:
            print(f"Validation ERROR: {e}", file=sys.stderr)
            return 1

    if args.command == "traffic-light":
        meta = parse_rob_csv(args.input, tool_type=tool_enum)
        svg_content = render_traffic_light_svg(
            meta=meta,
            title=args.title,
            show_symbols=not args.no_symbols,
            show_tooltips=not args.no_tooltips,
        )
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Traffic light plot successfully created -> {args.output} ({len(meta.assessments)} studies, {len(meta.domains)} domains)")
        return 0

    if args.command == "summary":
        meta = parse_rob_csv(args.input, tool_type=tool_enum)
        svg_content = render_summary_bar_svg(
            meta=meta,
            title=args.title,
            weighted=args.weighted,
        )
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Summary bar plot successfully created -> {args.output} ({'weighted' if args.weighted else 'unweighted'})")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
