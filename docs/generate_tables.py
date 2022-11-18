from pathlib import Path

import click
import pandas as pd
from disco.exceptions import EXCEPTIONS_TO_ERROR_CODES
from disco.models.upgrade_cost_analysis_generic_input_model import ThermalUpgradeParamsModel,\
    VoltageUpgradeParamsModel, UpgradeCostAnalysisSimulationModel
    
from  disco.models.upgrade_cost_analysis_generic_input_model import TotalUpgradeCostsResultModel, UpgradeViolationResultModel



@click.command()
@click.argument("output-dir", callback=lambda _, __, x: Path(x))
def generate_tables(output_dir):
    output_dir.mkdir(exist_ok=True, parents=True)
    generate_return_codes(output_dir)
    generate_upgrade_model_tables(output_dir)


def generate_return_codes(output_dir):
    output_file = output_dir / "return_codes.csv"
    with open(output_file, "w") as f_out:
        header = "Return Code,Description,Corrective Action"
        f_out.write("\t".join(header) + "\n")
        f_out.write("0,Success,\n")
        f_out.write("1,Generic error,\n")
        for item in EXCEPTIONS_TO_ERROR_CODES.values():
            f_out.write(str(item["error_code"]))
            f_out.write(",")
            f_out.write('"')
            f_out.write(item["description"])
            f_out.write('"')
            if item.get("corrective_action"):
                f_out.write(",")
                f_out.write('"')
                f_out.write(item["corrective_action"])
                f_out.write('"')
            f_out.write("\n")


def generate_upgrade_model_tables(output_dir):
    output_dir.mkdir(exist_ok=True, parents=True)
    for model in (
        ThermalUpgradeParamsModel,
        VoltageUpgradeParamsModel,
        UpgradeCostAnalysisSimulationModel,
        TotalUpgradeCostsResultModel,
        UpgradeViolationResultModel, 
    ):
        data = model.schema()
        df = pd.DataFrame.from_dict(data["properties"], orient='index')
        df.index.name="Input Parameter"
        df.reset_index(inplace=True)
        df = df.rename(columns={"description": "Description", "type": "Type", "default": "Default", "example": "Example"})
        df["Type"] = df["Type"].replace("number", "float")
        df["Required/Optional"] = "Optional"
        df.loc[~df["Example"].isna(), "Required/Optional"] = "Required"
        df["Example/Default"] = df["Default"].fillna(df["Example"])
        df = df[["Input Parameter", "Description", "Type", "Required/Optional", "Example/Default"]]
        filename = output_dir / (model.__name__ +".csv")
        df.to_csv(filename, index=False)
        print(f"Generated {filename}")


if __name__ == "__main__":
    generate_tables()
