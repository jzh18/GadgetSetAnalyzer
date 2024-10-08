#!/usr/bin/python3
"""
GadgetSetAnalyzer (GSA)
This static analysis tool compares an original binary with one or more variants derived from it to determine how a
software transformation or difference in binary production (e.g., compiler used, optimizations selected) impacts the
set of code-reuse gadgets available. Several metrics are generated by GSA, and are described in the README.

Dependencies:
GSA uses the common tool <ROPgadget> under the hood to obtain a gadget catalog. Output of sensitive addresses uses the
<angr> library.

"""

# Standard Library Imports
import argparse
import sys

# Third Party Imports


# Local Imports
from utility import *
from static_analyzer.GadgetSet import GadgetSet
from static_analyzer.GadgetStats import GadgetStats

LINE_SEP= "\n" # line separator

# Parse Arguments
parser = argparse.ArgumentParser()
parser.add_argument("original", help="Original program binary or directory of binaries.", type=str)
parser.add_argument("--variants", 
                    metavar="VARIANT=PATH",
                    nargs='+',
                    help="Sequence of variant names and variant paths.  Example: <variant_name1>=<file_path1> <variant_name1>=<file_path1>' ",
                    type=str)
parser.add_argument("--output_metrics", help="Output metric data as a CSV file.", action='store_true')
parser.add_argument("--output_addresses", help="Output addresses of sensitive gadgets as a CSV file. Ignored if --output_metrics is not specified.", action='store_true')
parser.add_argument("--output_tables", help="Output metric data as tables in LaTeX format. Ignored if --output_metrics is not specified. If specified, provide a row label, such as the program name.", action='store', type=str, default='')
parser.add_argument("--result_folder_name", help="Optionally specifies a specific output file name for the results folder.", action="store", type=str)
parser.add_argument("--original_name", help="Optionally specifies a specific name for the 'original' binary.", action="store", type=str, default="Original")
parser.add_argument("--output_console", help="Output gadget set and comparison data to console.", action="store_true")
parser.add_argument("--output_locality", help="Output gadget locality metric as a CSV file. Ignored if --output_metrics is not specified.", action='store_true')
parser.add_argument("--output_simple", help="Output simplified version of results in single file. Ignored if --output_metrics is not specified.", action='store_true')
args = parser.parse_args()
args.output_locality = args.output_locality or args.output_simple # enable locality if output_simple because output_simple uses locality

variants_dict = {}
for variant in args.variants:
    parts = variant.split("=")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        print("Error: variants are not in proper format")
        exit(1)
    variants_dict[parts[0]] = parts[1]

print("Starting Gadget Set Analyzer")

# Create Gadget sets for original
print("Analyzing original package [" + args.original_name + "] located at: " + args.original)
original = GadgetSet(args.original_name, args.original, False, args.output_console)

if not args.output_metrics:
    # Iterate through variants and compare, output to console.
    for key in variants_dict.keys():
        filepath = variants_dict.get(key)
        print("Analyzing variant package [" + key + "] located at: " + filepath)

        variant = GadgetSet(key, filepath, args.output_addresses, args.output_console)
        stat = GadgetStats(original, variant, args.output_console, args.output_locality)

# Prepare output lines for files
else:
    # Create a timestamped results folder
    try:
        if args.result_folder_name is None:
            directory_name = create_output_directory("results/analyzer_results_")
        else:
            directory_name = create_output_directory("results/" + args.result_folder_name, False)
    except OSError as osErr:
        print("An OS Error occurred during creation of results directory: " + osErr.strerror)
        sys.exit("Results cannot be logged, aborting operation...")
    print("Writing metrics files to " + directory_name)

    rate_format = "{:.1%}"
    float_format = "{:.2f}"

    # Prepare simplified file output for original if indicated
    if args.output_simple:
        simple_lines = ["Variant Name,Expressivity,Quality,Locality,S.P. Types,Syscall Available" + LINE_SEP]
        orig_metrics = original.name + "," + str(original.practical_ROP_expressivity) + ","
        orig_metrics = orig_metrics + float_format.format(original.average_functional_quality) + ","
        orig_metrics = orig_metrics + "NA,"
        orig_metrics = orig_metrics + str(original.total_sp_types) + ","
        orig_metrics = orig_metrics + str(len(original.SyscallGadgets)) + LINE_SEP
        simple_lines.append(orig_metrics)

    else:
        # Prepare file line arrays
        # Output file 1: Gadget Counts/Reduction, Total and by Category
        file_1_lines = ["Package Variant,Total Gadgets,ROP Gadgets,JOP Gadgets,COP Gadgets,Special Purpose Gadgets" + LINE_SEP]
        orig_counts = original.name + "," + str(original.total_unique_gadgets)
        orig_counts = orig_counts + "," + str(len(original.ROPGadgets))
        orig_counts = orig_counts + "," + str(len(original.JOPGadgets))
        orig_counts = orig_counts + "," + str(len(original.COPGadgets))
        orig_counts = orig_counts + "," + str(original.total_sp_gadgets) + LINE_SEP
        file_1_lines.append(orig_counts)

        # Output file 2: Gadget Introduction Rates
        file_2_lines = ["Package Variant,Total Gadgets,Total Introduction Rate,ROP Gadgets,ROP Introduction Rate,JOP Gadgets,JOP Introduction Rate,COP Gadgets,COP Introduction Rate" + LINE_SEP]
        orig_counts = original.name + "," + str(original.total_unique_gadgets) + ", ,"
        orig_counts = orig_counts + str(len(original.ROPGadgets)) + ", ,"
        orig_counts = orig_counts + str(len(original.JOPGadgets)) + ", ,"
        orig_counts = orig_counts + str(len(original.COPGadgets)) + LINE_SEP
        file_2_lines.append(orig_counts)

        # Output file #3: SP Gadget Counts + Introduction
        file_3_lines = [
                        "Package Variant,Syscall Gadgets,JOP Dispatcher Gadgets,JOP Dataloader Gadgets,JOP Initializers,JOP Trampolines,COP Dispatcher Gadgets,COP Dataloader Gadgets,COP Initializers,COP Strong Trampoline Gadgets,COP Intra-stack Pivot Gadgets" + LINE_SEP]
        orig_counts = original.name + "," + str(len(original.SyscallGadgets))
        orig_counts = orig_counts + "," + str(len(original.JOPDispatchers))
        orig_counts = orig_counts + "," + str(len(original.JOPDataLoaders))
        orig_counts = orig_counts + "," + str(len(original.JOPInitializers))
        orig_counts = orig_counts + "," + str(len(original.JOPTrampolines))
        orig_counts = orig_counts + "," + str(len(original.COPDispatchers))
        orig_counts = orig_counts + "," + str(len(original.COPDataLoaders))
        orig_counts = orig_counts + "," + str(len(original.COPInitializers))
        orig_counts = orig_counts + "," + str(len(original.COPStrongTrampolines))
        orig_counts = orig_counts + "," + str(len(original.COPIntrastackPivots)) + LINE_SEP
        file_3_lines.append(orig_counts)

        # Output File 4: Special Purpose Gadget Introduction Counts/Rates
        file_4_lines = [
                        "Package Variant,Syscall Gadgets,Syscall Gadget Introduction Rate," +
                        "JOP Dispatcher Gadgets,JOP Dispatcher Gadget Introduction Rate," +
                        "JOP Dataloader Gadgets,JOP Dataloader Gadget Introduction Rate," +
                        "JOP Initializer Gadgets,JOP Initializer Gadget Introduction Rate," +
                        "JOP Trampoline Gadgets,JOP Trampoline Gadget Introduction Rate," +
                        "COP Dispatcher Gadgets,COP Dispatcher Gadget Introduction Rate," +
                        "COP Dataloader Gadgets,COP Dataloader Gadget Introduction Rate," +
                        "COP Initializer Gadgets,COP Initializer Gadget Introduction Rate," +
                        "COP Strong Trampoline Gadgets,COP Strong Trampoline Gadget Introduction Rate," +
                        "COP Intra-stack Pivot Gadgets,COP Intra-stack Pivot Gadget Introduction Rate" + LINE_SEP]
        orig_counts = original.name + "," + str(len(original.SyscallGadgets)) + ", ,"
        orig_counts = orig_counts + str(len(original.JOPDispatchers)) + ", ,"
        orig_counts = orig_counts + str(len(original.JOPDataLoaders)) + ", ,"
        orig_counts = orig_counts + str(len(original.JOPInitializers)) + ", ,"
        orig_counts = orig_counts + str(len(original.JOPTrampolines)) + ", ,"
        orig_counts = orig_counts + str(len(original.COPDispatchers)) + ", ,"
        orig_counts = orig_counts + str(len(original.COPDataLoaders)) + ", ,"
        orig_counts = orig_counts + str(len(original.COPInitializers)) + ", ,"
        orig_counts = orig_counts + str(len(original.COPStrongTrampolines)) + ", ,"
        orig_counts = orig_counts + str(len(original.COPIntrastackPivots)) + LINE_SEP
        file_4_lines.append(orig_counts)

        # Output File 5: Gadget Expressivity Classes Fulfilled By Variant
        orig_prac_rop = str(original.practical_ROP_expressivity) + " of 11"
        orig_ASLR_prac_rop = str(original.practical_ASLR_ROP_expressivity) + " of 35"
        orig_simple_tc = str(original.turing_complete_ROP_expressivity) + " of 17"
        file_5_lines = ["Package Variant,Practical ROP Exploit,ASLR-Proof Practical ROP Exploit,Simple Turing Completeness" + LINE_SEP]
        orig_counts = original.name + ","
        orig_counts = orig_counts + orig_prac_rop + ","
        orig_counts = orig_counts + orig_ASLR_prac_rop + ","
        orig_counts = orig_counts + orig_simple_tc + LINE_SEP
        file_5_lines.append(orig_counts)

        # Output File 6: Overall Gadget Locality
        file_6_lines = ["Package Variant,Gadget Locality" + LINE_SEP]

        # Output File 7: Average Gadget Quality (and count of quality functional gadgets)
        file_7_lines = ["Package Variant,Quality ROP Gadgets,Average ROP Gadget Quality,Quality JOP Gadgets,Average JOP Gadget Quality,Quality COP Gadgets,Average COP Gadget Quality" + LINE_SEP]
        orig_quality = original.name + "," + str(len(original.ROPGadgets)) + "," + str(original.averageROPQuality)
        orig_quality += "," + str(len(original.JOPGadgets)) + "," + str(original.averageJOPQuality)
        orig_quality += "," + str(len(original.COPGadgets)) + "," + str(original.averageCOPQuality) + LINE_SEP
        file_7_lines.append(orig_quality)

        # Output File 8: Suspected function names containing introduced special purpose gadgets.
        file_8_lines = []
        if args.output_addresses:
            print("Writing function names associated with special purpose gadgets to disk.")

        # Output File 9: LaTeX formatted table data
        table_lines = ["" for i in range(4)]
        if args.output_tables != '':
            print("Writing LaTeX formatted table data to disk.")
            table_lines[0] = args.output_tables + " & " + str(original.total_unique_gadgets)
            table_lines[1] = args.output_tables + " & " + str(original.practical_ROP_expressivity) + "/" + str(original.practical_ASLR_ROP_expressivity) + "/" + str(original.turing_complete_ROP_expressivity)
            table_lines[2] = args.output_tables + " & " + str(original.total_functional_gadgets) + " / " + float_format.format(original.average_functional_quality)
            table_lines[3] = args.output_tables + " & " + str(original.total_sp_types)

    # Iterate through the variants. Scan them to get a gadget set, compare it to the original, add data to output files
    for key in variants_dict.keys():
        filepath = variants_dict.get(key)
        print("Analyzing variant package [" + key + "] located at: " + filepath)

        variant = GadgetSet(key, filepath, args.output_addresses, args.output_console)
        stat = GadgetStats(original, variant, args.output_console, args.output_locality)

        # Prepare simplified file output for original if indicated
        if args.output_simple:
            stat_metrics = variant.name + "," + str(stat.practical_ROP_exp_diff) + ","
            stat_metrics = stat_metrics + float_format.format(stat.total_average_quality_diff) + ","
            stat_metrics = stat_metrics + fmt_percent_keep_precision(stat.gadgetLocality) + "," # do not round locality
            stat_metrics = stat_metrics + str(stat.total_sp_type_reduction) + ","
            stat_metrics = stat_metrics + str(stat.SysCountDiff) + LINE_SEP
            simple_lines.append(stat_metrics)

        else:
            # Output file 1 variant lines
            stat_counts = variant.name + "," + str(variant.total_unique_gadgets) + " (" + str(stat.totalUniqueCountDiff) + "; " + rate_format.format(stat.totalUniqueCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.ROPGadgets)) + " (" + str(stat.ROPCountDiff) + "; " + rate_format.format(stat.ROPCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.JOPGadgets)) + " (" + str(stat.JOPCountDiff) + "; " + rate_format.format(stat.JOPCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.COPGadgets)) + " (" + str(stat.COPCountDiff) + "; " + rate_format.format(stat.COPCountReduction) + "),"
            stat_counts = stat_counts + str(variant.total_sp_gadgets) + " (" + str(stat.total_sp_count_diff) + "; " + rate_format.format(stat.total_sp_reduction) + ")" + LINE_SEP
            file_1_lines.append(stat_counts)

            # Output file 2 variant lines
            stat_counts = variant.name + "," + str(variant.total_unique_gadgets) + ","
            stat_counts = stat_counts + rate_format.format(stat.totalUniqueIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.ROPGadgets)) + ","
            stat_counts = stat_counts + rate_format.format(stat.ROPIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.JOPGadgets)) + ","
            stat_counts = stat_counts + rate_format.format(stat.JOPIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.COPGadgets)) + ","
            stat_counts = stat_counts + rate_format.format(stat.COPIntroductionRate) + LINE_SEP
            file_2_lines.append(stat_counts)

            # Output file 3 variant lines
            stat_counts = variant.name + "," + str(len(variant.SyscallGadgets)) + " (" + str(
                stat.SysCountDiff) + "; " + rate_format.format(stat.SysCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.JOPDispatchers)) + " (" + str(
                stat.JOPDispatchersCountDiff) + "; " + rate_format.format(stat.JOPDispatchersCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.JOPDataLoaders)) + " (" + str(
                stat.JOPDataLoadersCountDiff) + "; " + rate_format.format(stat.JOPDataLoadersCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.JOPInitializers)) + " (" + str(
                stat.JOPInitializersCountDiff) + "; " + rate_format.format(stat.JOPInitializersCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.JOPTrampolines)) + " (" + str(
                stat.JOPTrampolinesCountDiff) + "; " + rate_format.format(stat.JOPTrampolinesCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.COPDispatchers)) + " (" + str(
                stat.COPDispatchersCountDiff) + "; " + rate_format.format(stat.COPDispatchersCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.COPDataLoaders)) + " (" + str(
                stat.COPDataLoadersCountDiff) + "; " + rate_format.format(stat.COPDataLoadersCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.COPInitializers)) + " (" + str(
                stat.COPInitializersCountDiff) + "; " + rate_format.format(stat.COPInitializersCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.COPStrongTrampolines)) + " (" + str(
                stat.COPStrongTrampolinesCountDiff) + "; " + rate_format.format(
                stat.COPStrongTrampolinesCountReduction) + "),"
            stat_counts = stat_counts + str(len(variant.COPIntrastackPivots)) + " (" + str(
                stat.COPIntrastackPivotsCountDiff) + "; " + rate_format.format(
                stat.COPIntrastackPivotsCountReduction) + ")" + LINE_SEP
            file_3_lines.append(stat_counts)

            # Output file 4 variant lines
            stat_counts = variant.name + "," + str(len(variant.SyscallGadgets)) + ","
            stat_counts = stat_counts + rate_format.format(stat.SysIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.JOPDispatchers)) + ","
            stat_counts = stat_counts + rate_format.format(stat.JOPDispatchersIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.JOPDataLoaders)) + ","
            stat_counts = stat_counts + rate_format.format(stat.JOPDataLoadersIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.JOPInitializers)) + ","
            stat_counts = stat_counts + rate_format.format(stat.JOPInitializersIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.JOPTrampolines)) + ","
            stat_counts = stat_counts + rate_format.format(stat.JOPTrampolinesIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.COPDispatchers)) + ","
            stat_counts = stat_counts + rate_format.format(stat.COPDispatchersIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.COPDataLoaders)) + ","
            stat_counts = stat_counts + rate_format.format(stat.COPDataLoadersIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.COPInitializers)) + ","
            stat_counts = stat_counts + rate_format.format(stat.COPInitializersIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.COPStrongTrampolines)) + ","
            stat_counts = stat_counts + rate_format.format(stat.COPStrongTrampolinesIntroductionRate) + ","
            stat_counts = stat_counts + str(len(variant.COPIntrastackPivots)) + ","
            stat_counts = stat_counts + rate_format.format(stat.COPIntrastackPivotsIntroductionRate) + LINE_SEP
            file_4_lines.append(stat_counts)

            # Output file 5 variant lines
            stat_counts = variant.name + "," + str(variant.practical_ROP_expressivity) + " (" + str(stat.practical_ROP_exp_diff) + "),"
            stat_counts += str(variant.practical_ASLR_ROP_expressivity) + " (" + str(stat.practical_ASLR_ROP_exp_diff)  + "),"
            stat_counts += str(variant.turing_complete_ROP_expressivity) + " (" + str(stat.turing_complete_ROP_exp_diff) + ")" + LINE_SEP
            file_5_lines.append(stat_counts)

            # Output file 6 variant lines
            if args.output_locality:
                stat_locality = variant.name + "," + fmt_percent_keep_precision(stat.gadgetLocality) + LINE_SEP
                file_6_lines.append(stat_locality)

            # Output file 7 variant lines
            stat_quality = variant.name + "," + str(len(variant.ROPGadgets)) + " (" + str(stat.keptQualityROPCountDiff) + "),"
            stat_quality += str(variant.averageROPQuality) + " (" + str(stat.averageROPQualityDiff) + "),"
            stat_quality += str(len(variant.JOPGadgets)) + " (" + str(stat.keptQualityJOPCountDiff) + "),"
            stat_quality += str(variant.averageJOPQuality) + " (" + str(stat.averageJOPQualityDiff) + "),"
            stat_quality += str(len(variant.COPGadgets)) + " (" + str(stat.keptQualityCOPCountDiff) + "),"
            stat_quality += str(variant.averageCOPQuality) + " (" + str(stat.averageCOPQualityDiff) + ")" + LINE_SEP
            file_7_lines.append(stat_quality)

            # Output file 8 variant lines
            if args.output_addresses:
                file_8_lines.append("Sensitive gadgets introduced in variant: " + variant.name + LINE_SEP)
                specialSets = [variant.SyscallGadgets, variant.JOPDispatchers,
                            variant.JOPDataLoaders, variant.JOPInitializers,
                            variant.JOPTrampolines, variant.COPDispatchers,
                            variant.COPDataLoaders, variant.COPInitializers,
                            variant.COPStrongTrampolines, variant.COPIntrastackPivots]
                for specialSet in specialSets:
                    for gadget in specialSet:
                        file_8_lines.append("Gadget: " + str(gadget.instructions) + LINE_SEP)
                        file_8_lines.append("Found at offset: " + gadget.offset + LINE_SEP)
                        function = variant.getFunction(gadget.offset)
                        if function is None:
                            file_8_lines.append("No associated function found." + LINE_SEP)
                        else:
                            file_8_lines.append("Most likely location in source code: " + function + LINE_SEP)
                file_8_lines.append("----------------------------------------------------------" + LINE_SEP)

            # Output File 9 variant lines
            if args.output_tables != '':
                table_lines[0] = table_lines[0] + " & " + str(variant.total_unique_gadgets) + " (" + rate_format.format(stat.totalUniqueIntroductionRate) + ")"
                table_lines[1] = table_lines[1] + " & " + str(variant.practical_ROP_expressivity) + "/" + str(variant.practical_ASLR_ROP_expressivity) + "/" + str(variant.turing_complete_ROP_expressivity) + " & (" + \
                    str(stat.practical_ROP_exp_diff) + "/" + str(stat.practical_ASLR_ROP_exp_diff) + "/" + str(stat.turing_complete_ROP_exp_diff) + ")"
                table_lines[2] = table_lines[2] +  " & " + str(variant.total_functional_gadgets) + " / " + float_format.format(variant.average_functional_quality) + " & (" + \
                    str(stat.total_functional_count_diff) + " / " + float_format.format(stat.total_average_quality_diff) + ")"
                table_lines[3] = table_lines[3] + " & " + str(variant.total_sp_types) + " & (" + str(stat.total_sp_type_reduction) + ")"

    # Write file lines to disk.
    try:
        if args.output_simple:
            # Output Simplified Results
            file = open(directory_name + "/GadgetSetAnalysis.csv", "w")
            file.writelines(simple_lines)
            file.close()

        else:
            # Output file 1
            file = open(directory_name + "/GadgetCounts_Reduction.csv", "w")
            file.writelines(file_1_lines)
            file.close()

            # Output file 2
            file = open(directory_name + "/Gadget_Introduction_Counts_Rate.csv", "w")
            file.writelines(file_2_lines)
            file.close()

            # Output file 3
            file = open(directory_name + "/SpecialPurpose_GadgetCounts_Reduction.csv", "w")
            file.writelines(file_3_lines)
            file.close()

            # Output file 4
            file = open(directory_name + "/SpecialPurpose_Gadget_Introduction_Counts_Rate.csv", "w")
            file.writelines(file_4_lines)
            file.close()

            # Output file 5
            file = open(directory_name + "/Expressivity_Counts.csv", "w")
            file.writelines(file_5_lines)
            file.close()

            # Output file 6
            if args.output_locality:
                file = open(directory_name + "/Gadget Locality.csv", "w")
                file.writelines(file_6_lines)
                file.close()

            # Output file 7
            file = open(directory_name + "/Gadget Quality.csv", "w")
            file.writelines(file_7_lines)
            file.close()

            # Output file 8
            if args.output_addresses:
                file = open(directory_name + "/Likely_Gadget_Locations.txt", "w")
                file.writelines(file_8_lines)
                file.close()

            if args.output_tables != '':
                table_lines[0] = table_lines[0] + " \\\\ " + LINE_SEP
                table_lines[1] = table_lines[1] + " \\\\ " + LINE_SEP
                table_lines[2] = table_lines[2] + " \\\\ " + LINE_SEP
                table_lines[3] = table_lines[3] + " \\\\ " + LINE_SEP
                file = open(directory_name + "/Table_Formatted.txt", "w")
                file.writelines(table_lines)
                file.close()
    except OSError as osErr:
        print(osErr)
