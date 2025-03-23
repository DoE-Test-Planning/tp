from typing import Dict, List, Any, Optional, Set
import itertools
import allpairspy
from pyDOE2 import fracfact
import pandas as pd
import numpy as np
import json


class DoEGenerator:
    """
    Design of Experiments (DoE) generator service.
    
    Generates test scenarios based on provided parameters and values.
    Implements various test reduction techniques.
    """
    
    @staticmethod
    def generate_all_combinations(parameter_sets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate all possible combinations of parameters (full factorial design).
        
        Args:
            parameter_sets: List of parameter sets, each with name and list of parameters
            
        Returns:
            List of test scenarios with all possible combinations
        """
        # Extract parameters from parameter sets
        all_params = []
        param_names = []
        
        for ps in parameter_sets:
            for param in ps["parameters"]:
                all_params.append((f"{ps['name']}.{param['name']}", param["value"]))
                param_names.append(f"{ps['name']}.{param['name']}")
        
        # Generate all combinations
        all_combinations = list(itertools.product([0, 1], repeat=len(all_params)))
        
        # Create test scenarios
        scenarios = []
        
        for i, combination in enumerate(all_combinations):
            scenario = {"id": i + 1, "parameters": {}}
            
            for j, param in enumerate(all_params):
                if combination[j] == 1:
                    scenario["parameters"][param[0]] = param[1]
            
            scenarios.append(scenario)
        
        return scenarios
    
    @staticmethod
    def reduce_pairwise(parameter_sets: List[Dict[str, Any]], parameters_to_include: List[str] = None) -> List[Dict[str, Any]]:
        """
        Reduce test scenarios using pairwise testing.
        
        Args:
            parameter_sets: List of parameter sets, each with name and list of parameters
            parameters_to_include: List of parameter names that must be included in all scenarios
            
        Returns:
            List of reduced test scenarios using pairwise testing
        """
        # Extract parameters from parameter sets
        all_params = []
        param_values = {}
        
        for ps in parameter_sets:
            for param in ps["parameters"]:
                full_name = f"{ps['name']}.{param['name']}"
                param_values[full_name] = [0, 1]  # Binary options (include or not)
                all_params.append(full_name)
        
        # Configure parameters to include in all scenarios
        constraints = []
        if parameters_to_include:
            for param_name in parameters_to_include:
                constraints.append(lambda values: values[param_name] == 1)
        
        # Generate pairwise combinations
        pairwise_params = allpairspy.AllPairs(param_values, filter_func=constraints if constraints else None)
        
        # Create test scenarios
        scenarios = []
        
        for i, combination in enumerate(pairwise_params):
            scenario = {"id": i + 1, "parameters": {}}
            
            for j, param_name in enumerate(all_params):
                if combination[j] == 1:
                    # Extract the parameter value from original data
                    ps_name, param_name_only = param_name.split(".", 1)
                    for ps in parameter_sets:
                        if ps["name"] == ps_name:
                            for param in ps["parameters"]:
                                if param["name"] == param_name_only:
                                    scenario["parameters"][param_name] = param["value"]
                                    break
            
            scenarios.append(scenario)
        
        return scenarios
    
    @staticmethod
    def reduce_fractional_factorial(parameter_sets: List[Dict[str, Any]], parameters_to_include: List[str] = None) -> List[Dict[str, Any]]:
        """
        Reduce test scenarios using fractional factorial design.
        
        Args:
            parameter_sets: List of parameter sets, each with name and list of parameters
            parameters_to_include: List of parameter names that must be included in all scenarios
            
        Returns:
            List of reduced test scenarios using fractional factorial design
        """
        # Extract parameters from parameter sets
        all_params = []
        param_names = []
        
        for ps in parameter_sets:
            for param in ps["parameters"]:
                full_name = f"{ps['name']}.{param['name']}"
                all_params.append((full_name, param["value"]))
                param_names.append(full_name)
        
        # Determine the design resolution based on the number of parameters
        n_params = len(all_params)
        if n_params <= 3:
            # For 3 or fewer parameters, use full factorial design
            return DoEGenerator.generate_all_combinations(parameter_sets)
        
        # Determine the appropriate fractional design
        if n_params <= 7:
            design = fracfact(f"a{n_params-1}")  # 2^(k-1) design
        elif n_params <= 15:
            design = fracfact(f"a{n_params-2}")  # 2^(k-2) design
        else:
            design = fracfact(f"a{n_params-3}")  # 2^(k-3) design
        
        # Convert -1,1 to 0,1 for our parameter representation
        design = (design + 1) / 2
        
        # Create test scenarios
        scenarios = []
        
        for i, row in enumerate(design):
            scenario = {"id": i + 1, "parameters": {}}
            
            for j, val in enumerate(row):
                if val == 1 or (parameters_to_include and param_names[j] in parameters_to_include):
                    scenario["parameters"][param_names[j]] = all_params[j][1]
            
            scenarios.append(scenario)
        
        return scenarios
    
    @staticmethod
    def format_to_markdown(scenarios: List[Dict[str, Any]], parameter_sets: List[Dict[str, Any]]) -> str:
        """
        Format test scenarios as Markdown table.
        
        Args:
            scenarios: List of test scenarios
            parameter_sets: List of parameter sets used to generate scenarios
            
        Returns:
            Markdown formatted table
        """
        # Get all unique parameter names from scenarios
        all_params = set()
        for scenario in scenarios:
            all_params.update(scenario["parameters"].keys())
        
        # Sort parameters by their original order in parameter_sets
        ordered_params = []
        for ps in parameter_sets:
            for param in ps["parameters"]:
                full_name = f"{ps['name']}.{param['name']}"
                if full_name in all_params:
                    ordered_params.append(full_name)
        
        # Create the markdown table header
        markdown = "| Scenario |"
        for param in ordered_params:
            markdown += f" {param} |"
        markdown += "\n"
        
        # Add separator row
        markdown += "|" + "---|" * (len(ordered_params) + 1) + "\n"
        
        # Add scenario rows
        for scenario in scenarios:
            markdown += f"| {scenario['id']} |"
            
            for param in ordered_params:
                value = scenario["parameters"].get(param, "")
                markdown += f" {value} |"
            
            markdown += "\n"
        
        return markdown
    
    @staticmethod
    def format_to_dataframe(scenarios: List[Dict[str, Any]], parameter_sets: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Format test scenarios as pandas DataFrame (for Excel export).
        
        Args:
            scenarios: List of test scenarios
            parameter_sets: List of parameter sets used to generate scenarios
            
        Returns:
            Pandas DataFrame with test scenarios
        """
        # Get all unique parameter names from scenarios
        all_params = set()
        for scenario in scenarios:
            all_params.update(scenario["parameters"].keys())
        
        # Sort parameters by their original order in parameter_sets
        ordered_params = []
        for ps in parameter_sets:
            for param in ps["parameters"]:
                full_name = f"{ps['name']}.{param['name']}"
                if full_name in all_params:
                    ordered_params.append(full_name)
        
        # Create DataFrame
        df = pd.DataFrame(columns=["Scenario"] + ordered_params)
        
        # Add scenario rows
        for scenario in scenarios:
            row = {"Scenario": scenario["id"]}
            
            for param in ordered_params:
                row[param] = scenario["parameters"].get(param, "")
            
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        return df
    
    @staticmethod
    def calculate_file_sizes(scenarios: List[Dict[str, Any]], parameter_sets: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate sizes of export files.
        
        Args:
            scenarios: List of test scenarios
            parameter_sets: List of parameter sets used to generate scenarios
            
        Returns:
            Dictionary with MD and XLSX file sizes in bytes
        """
        # Calculate MD file size
        md_content = DoEGenerator.format_to_markdown(scenarios, parameter_sets)
        md_size = len(md_content.encode("utf-8"))
        
        # Estimate XLSX file size (rough estimation)
        df = DoEGenerator.format_to_dataframe(scenarios, parameter_sets)
        # A rough estimate based on the DataFrame size
        xlsx_size = len(df) * len(df.columns) * 20  # 20 bytes per cell is a rough estimate
        
        return {
            "md_size": md_size,
            "xlsx_size": xlsx_size
        } 