import pandas as pd
import argparse
import sys
import matplotlib.pyplot as plt
import seaborn as sns  # Ensure Seaborn is installed
import os
import matplotlib as mpl
import numpy as np

def print_contact_info():
    print("============================================")
    print("       Dr. Christian Tantardini")
    print(" Email: christiantantardini@ymail.com")
    print(" https://scholar.google.com/citations?user=QCZdlUQAAAAJ")
    print("============================================\n")

def load_data(input_file):
    """Load data from the input file into a pandas DataFrame."""
    try:
        data = pd.read_csv(
            input_file, sep=r'\s+', comment='#', header=None,
            names=[
                'Ef[unit]', 'T[K]', 'N[e/uc]', 'DOS(ef)[1/(Ha*uc)]', 'S[V/K]',
                'sigma/tau0[1/(ohm*m*s)]', 'RH[m**3/C]', 'kappae/tau0[W/(m*K*s)]',
                'cv[J/(mol*K)]', 'chi[m**3/mol]'
            ]
        )
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def detect_ef_unit(input_file):
    """Detect the unit of Ef by inspecting the header or first few lines."""
    unit_conversion = None
    try:
        with open(input_file, 'r') as file:
            for line in file:
                if line.startswith('#'):
                    if 'Ef[Ry]' in line:
                        unit_conversion = 'Ef[Ry]'
                        break
                    elif 'Ef[Ha]' in line:
                        unit_conversion = 'Ef[Ha]'
                        break
                    elif 'Ef[eV]' in line:
                        unit_conversion = 'Ef[eV]'
                        break
        if unit_conversion is None:
            print("Ef unit not specified in the header. Assuming 'Ef[eV]'.\n")
            unit_conversion = 'Ef[eV]'
        else:
            print(f"Detected Ef unit: {unit_conversion}\n")
        return unit_conversion
    except Exception as e:
        print(f"Error detecting Ef unit: {e}")
        sys.exit(1)

def convert_ef_to_eV(data, unit_conversion, rydberg_to_ev, hartree_to_ev):
    """Convert Ef to eV based on the detected unit."""
    try:
        if unit_conversion == 'Ef[Ry]':
            data['Ef[eV]'] = data['Ef[unit]'] * rydberg_to_ev
            print("Converted Ef from Rydberg to eV.\n")
        elif unit_conversion == 'Ef[Ha]':
            data['Ef[eV]'] = data['Ef[unit]'] * hartree_to_ev
            print("Converted Ef from Hartree to eV.\n")
        elif unit_conversion == 'Ef[eV]':
            data['Ef[eV]'] = data['Ef[unit]']
            print("Ef is already in eV. No conversion needed.\n")
        else:
            print("Unknown Ef unit. Cannot convert to eV.")
            sys.exit(1)
        return data
    except Exception as e:
        print(f"Error converting Ef to eV: {e}")
        sys.exit(1)

def subtract_fermi_energy(data, fermi_energy):
    """Subtract Fermi energy from Ef[eV]."""
    try:
        data['Ef[eV]'] -= fermi_energy
        print(f"Fermi energy of {fermi_energy} eV subtracted from Ef[eV].\n")
        return data
    except Exception as e:
        print(f"Error subtracting Fermi energy: {e}")
        sys.exit(1)

def convert_S(data, s_scale_factor):
    """Convert S from V/K to µV/K."""
    try:
        data['S[µV/K]'] = data['S[V/K]'] * s_scale_factor
        print("Converted Seebeck coefficient from V/K to µV/K.\n")
        return data
    except Exception as e:
        print(f"Error converting S to µV/K: {e}")
        sys.exit(1)

def get_available_mu_Ef(data):
    """Retrieve and return sorted unique (mu - E_F) values."""
    unique_mu_Ef = np.sort(data['Ef[eV]'].unique())
    return unique_mu_Ef

def find_closest_mu_Ef(input_value, available_values, tolerance=0.001):
    """Find the closest (mu - E_F) value within the specified tolerance."""
    idx = (np.abs(available_values - input_value)).argmin()
    closest_value = available_values[idx]
    if np.abs(closest_value - input_value) <= tolerance:
        return closest_value
    else:
        return None

def plot_S_vs_mu_Ef(data, temperatures, output_dir, palette):
    """Plot S vs (mu - E_F) for each chosen T and save data to CSV."""
    plt.figure(figsize=(10, 7))
    for idx, T in enumerate(temperatures):
        subset = data[data['T[K]'] == T]
        if subset.empty:
            print(f"Warning: No data found for T = {T} K.")
            continue

        # Save the data used for this plot
        csv_filename = os.path.join(output_dir, f'S_vs_mu_Ef_T_{T}_K.csv')
        subset.to_csv(csv_filename, index=False)
        print(f"Data for T = {T} K saved to '{csv_filename}'.")

        plt.plot(
            subset['Ef[eV]'], 
            subset['S[µV/K]'], 
            linestyle='-', 
            linewidth=2, 
            color=palette[idx % len(palette)],
            label=rf'T = {T} K'
        )
    if plt.gca().has_data():
        plt.xlabel(r'$\mu - E_F$ (eV)', fontsize=16)
        plt.ylabel(r'$S$ ($\mu$V/K)', fontsize=16)
        plt.title(r'Seebeck Coefficient vs $\mu - E_F$', fontsize=18)
        plt.legend(title='Temperature (K)', fontsize=14, title_fontsize=16, loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plot_filename_png = os.path.join(output_dir, 'S_vs_mu_Ef.png')
        plot_filename_pdf = os.path.join(output_dir, 'S_vs_mu_Ef.pdf')
        plt.savefig(plot_filename_png, dpi=300, bbox_inches='tight')
        plt.savefig(plot_filename_pdf, bbox_inches='tight')
        plt.close()
        print(f"Plot 'S_vs_mu_Ef' saved as PNG and PDF in '{output_dir}'.\n")
    else:
        plt.close()
        print("No plots were generated for S vs μ - E_F due to missing data.\n")

def plot_S_vs_T(data, mu_Ef_values, output_dir, palette, available_mu_Ef, tolerance=0.001):
    """Plot S vs T for each chosen (mu - E_F) and save data to CSV."""
    plt.figure(figsize=(10, 7))
    for idx, mu_Ef in enumerate(mu_Ef_values):
        subset = data[np.isclose(data['Ef[eV]'], mu_Ef, atol=tolerance)]
        if subset.empty:
            print(f"Warning: No data found for μ - E_F = {mu_Ef:.3f} eV within tolerance.")
            continue

        # Save the data used for this plot
        csv_filename = os.path.join(output_dir, f'S_vs_T_mu_Ef_{mu_Ef:.3f}_eV.csv')
        subset.to_csv(csv_filename, index=False)
        print(f"Data for μ - E_F = {mu_Ef:.3f} eV saved to '{csv_filename}'.")

        plt.plot(
            subset['T[K]'], 
            subset['S[µV/K]'], 
            linestyle='-', 
            linewidth=2, 
            color=palette[idx % len(palette)],
            label=rf'$\mu - E_F$ = {mu_Ef:.3f} eV'
        )
    if plt.gca().has_data():
        plt.xlabel('Temperature (K)', fontsize=16)
        plt.ylabel(r'$S$ ($\mu$V/K)', fontsize=16)
        plt.title('Seebeck Coefficient vs Temperature', fontsize=18)
        plt.legend(title=r'$\mu - E_F$ (eV)', fontsize=14, title_fontsize=16, loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plot_filename_png = os.path.join(output_dir, 'S_vs_T.png')
        plot_filename_pdf = os.path.join(output_dir, 'S_vs_T.pdf')
        plt.savefig(plot_filename_png, dpi=300, bbox_inches='tight')
        plt.savefig(plot_filename_pdf, bbox_inches='tight')
        plt.close()
        print(f"Plot 'S_vs_T' saved as PNG and PDF in '{output_dir}'.\n")
    else:
        plt.close()
        print("No plots were generated for S vs T due to missing data.\n")

def plot_sigma_vs_T(data, mu_Ef_values, output_dir, palette, available_mu_Ef, tolerance=0.001):
    """Plot sigma/tau0 vs T for each chosen (mu - E_F) and save data to CSV."""
    plt.figure(figsize=(10, 7))
    for idx, mu_Ef in enumerate(mu_Ef_values):
        subset = data[np.isclose(data['Ef[eV]'], mu_Ef, atol=tolerance)]
        if subset.empty:
            print(f"Warning: No data found for μ - E_F = {mu_Ef:.3f} eV within tolerance.")
            continue

        # Save the data used for this plot
        csv_filename = os.path.join(output_dir, f'sigma_vs_T_mu_Ef_{mu_Ef:.3f}_eV.csv')
        subset.to_csv(csv_filename, index=False)
        print(f"Data for μ - E_F = {mu_Ef:.3f} eV saved to '{csv_filename}'.")

        plt.plot(
            subset['T[K]'], 
            subset['sigma/tau0[1/(ohm*m*s)]'], 
            linestyle='-', 
            linewidth=2, 
            color=palette[idx % len(palette)],
            label=rf'$\mu - E_F$ = {mu_Ef:.3f} eV'
        )
    if plt.gca().has_data():
        plt.xlabel('Temperature (K)', fontsize=16)
        plt.ylabel(r'$\sigma/\tau_0$ [1/(Ohm·m·s)]', fontsize=16)
        plt.title('Electrical Conductivity vs Temperature', fontsize=18)
        plt.legend(title=r'$\mu - E_F$ (eV)', fontsize=14, title_fontsize=16, loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plot_filename_png = os.path.join(output_dir, 'sigma_vs_T.png')
        plot_filename_pdf = os.path.join(output_dir, 'sigma_vs_T.pdf')
        plt.savefig(plot_filename_png, dpi=300, bbox_inches='tight')
        plt.savefig(plot_filename_pdf, bbox_inches='tight')
        plt.close()
        print(f"Plot 'sigma_vs_T' saved as PNG and PDF in '{output_dir}'.\n")
    else:
        plt.close()
        print("No plots were generated for σ/τ₀ vs T due to missing data.\n")

def plot_kappae_vs_T(data, mu_Ef_values, output_dir, palette, available_mu_Ef, tolerance=0.001):
    """Plot kappae/tau0 vs T for each chosen (mu - E_F) and save data to CSV."""
    plt.figure(figsize=(10, 7))
    for idx, mu_Ef in enumerate(mu_Ef_values):
        subset = data[np.isclose(data['Ef[eV]'], mu_Ef, atol=tolerance)]
        if subset.empty:
            print(f"Warning: No data found for μ - E_F = {mu_Ef:.3f} eV within tolerance.")
            continue

        # Save the data used for this plot
        csv_filename = os.path.join(output_dir, f'kappae_vs_T_mu_Ef_{mu_Ef:.3f}_eV.csv')
        subset.to_csv(csv_filename, index=False)
        print(f"Data for μ - E_F = {mu_Ef:.3f} eV saved to '{csv_filename}'.")

        plt.plot(
            subset['T[K]'], 
            subset['kappae/tau0[W/(m*K*s)]'], 
            linestyle='-', 
            linewidth=2, 
            color=palette[idx % len(palette)],
            label=rf'$\mu - E_F$ = {mu_Ef:.3f} eV'
        )
    if plt.gca().has_data():
        plt.xlabel('Temperature (K)', fontsize=16)
        plt.ylabel(r'$\kappa_e/\tau_0$ [W/(m·K·s)]', fontsize=16)
        plt.title('Electronic Thermal Conductivity vs Temperature', fontsize=18)
        plt.legend(title=r'$\mu - E_F$ (eV)', fontsize=14, title_fontsize=16, loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plot_filename_png = os.path.join(output_dir, 'kappae_vs_T.png')
        plot_filename_pdf = os.path.join(output_dir, 'kappae_vs_T.pdf')
        plt.savefig(plot_filename_png, dpi=300, bbox_inches='tight')
        plt.savefig(plot_filename_pdf, bbox_inches='tight')
        plt.close()
        print(f"Plot 'kappae_vs_T' saved as PNG and PDF in '{output_dir}'.\n")
    else:
        plt.close()
        print("No plots were generated for κₑ/τ₀ vs T due to missing data.\n")

def get_user_choice(prompt, choices):
    """Utility function to get a valid user choice."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in choices:
            return choice
        else:
            print(f"Invalid choice. Please choose from {choices}.\n")

def get_multiple_values(prompt, available_values, value_type=float, tolerance=0.001):
    """Utility function to get multiple values from the user."""
    while True:
        user_input = input(prompt).strip()
        try:
            input_values = [value_type(val) for val in user_input.split(',') if val.strip()]
            matched_values = []
            for val in input_values:
                closest_val = find_closest_mu_Ef(val, available_values, tolerance)
                if closest_val is not None:
                    matched_values.append(closest_val)
                else:
                    print(f"No (μ - E_F) value found within ±{tolerance} eV of {val:.3f} eV.")
            if matched_values:
                return matched_values
            else:
                print("None of the entered values matched within the tolerance. Please try again.\n")
        except ValueError:
            print(f"Invalid input. Please enter comma-separated {value_type.__name__} values.\n")

def main():
    print_contact_info()

    # Conversion factors
    rydberg_to_ev = 13.605698  # Rydberg to eV
    hartree_to_ev = 27.211386  # Hartree to eV
    s_scale_factor = 1e6  # To display S in units of µV/K

    # Set up argument parser for initial data processing
    parser = argparse.ArgumentParser(
        description=r"""
**BTP2 Data Extraction and Plotting Script**

This script processes a space-separated data file containing various physical properties and generates high-quality plots suitable for publication. It offers functionalities such as unit conversion, Fermi energy adjustment, and multiple plotting options.

**Functionalities:**
1. **Unit Conversion:** Automatically detects the unit of Ef (Rydberg, Hartree, or eV) and converts it to eV if necessary.
2. **Fermi Energy Adjustment:** Optionally subtracts the provided Fermi energy from Ef[eV].
3. **Plotting Capabilities:**
   - **Option 1:** Plot S vs (μ - E_F) for chosen temperature(s).
   - **Option 2:** Plot S vs T for chosen (μ - E_F) value(s).
   - **Option 3:** Plot σ/τ₀ vs T for chosen (μ - E_F) value(s).
   - **Option 4:** Plot κₑ/τ₀ vs T for chosen (μ - E_F) value(s).
   - **Option 5:** Exit.

**Input File Format:**
- Space-separated text file containing columns:
  ['Ef[unit]', 'T[K]', 'N[e/uc]', 'DOS(ef)[1/(Ha*uc)]', 'S[V/K]',
  'sigma/tau0[1/(ohm*m*s)]', 'RH[m**3/C]', 'kappae/tau0[W/(m*K*s)]',
  'cv[J/(mol*K)]', 'chi[m**3/mol]']
- Lines beginning with '#' are treated as comments and ignored.

**Usage:**
python BTP2-extract.py -i data.txt
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required argument
    parser.add_argument('-i', '--input', required=True, help='Path to the input file containing the data (e.g., data.txt)')
    args = parser.parse_args()

    # Load and process data
    data = load_data(args.input)
    unit_conversion = detect_ef_unit(args.input)
    data = convert_ef_to_eV(data, unit_conversion, rydberg_to_ev, hartree_to_ev)

    # Interactive prompt for subtracting Fermi energy
    subtract_choice = get_user_choice("Do you want to subtract the Fermi energy from μ? (yes/no): ", ['yes', 'no'])
    if subtract_choice == 'yes':
        fermi_energy = None
        while fermi_energy is None:
            try:
                fermi_input = input("Enter the Fermi energy in eV to subtract from μ (e.g., 5.0): ").strip()
                fermi_energy = float(fermi_input)
            except ValueError:
                print("Invalid input. Please enter a numerical value for the Fermi energy.\n")
        data = subtract_fermi_energy(data, fermi_energy)
    else:
        print("Proceeding without subtracting Fermi energy from μ.\n")

    # Convert S from V/K to µV/K
    data = convert_S(data, s_scale_factor)

    # Ensure plots directory exists
    plots_dir = 'plots'
    os.makedirs(plots_dir, exist_ok=True)

    # Apply a professional matplotlib style
    sns.set_style("whitegrid")
    palette = sns.color_palette("tab10")
    mpl.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 16,
        'axes.titlesize': 18,
        'legend.fontsize': 14,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'figure.figsize': (10, 7),
        'lines.linewidth': 2,
        'grid.color': '0.8',
        'grid.linestyle': '--',
        'legend.frameon': False
    })

    # Get available (mu - E_F) values
    available_mu_Ef = get_available_mu_Ef(data)

    # Interactive plotting options
    while True:
        print("Select a plotting option:")
        print("1. Plot S vs (μ - E_F) for chosen T(s) and save .csv file.")
        print("2. Plot S vs T for chosen (μ - E_F) value(s) and save .csv file.")
        print("3. Plot σ/τ₀ vs T for chosen (μ - E_F) value(s) and save .csv file.")
        print("4. Plot κₑ/τ₀ vs T for chosen (μ - E_F) value(s) and save .csv file.")
        print("5. Exit.")

        choice = get_user_choice("Enter the number corresponding to your choice (1-5): ", ['1', '2', '3', '4', '5'])
        print()

        if choice == '1':
            temperatures = []
            while not temperatures:
                try:
                    temp_input = input("Enter temperature(s) in K separated by commas (e.g., 300,400,500): ").strip()
                    temperatures = [float(val) for val in temp_input.split(',') if val.strip()]
                    if not temperatures:
                        print("No temperatures entered. Please try again.\n")
                except ValueError:
                    print("Invalid input. Please enter numerical values for temperatures.\n")
            plot_S_vs_mu_Ef(data, temperatures, plots_dir, palette)

        elif choice == '2':
            mu_Ef_values = get_multiple_values(
                "Enter (μ - E_F) value(s) in eV separated by commas (e.g., 1.000,2.000,3.000): ",
                available_mu_Ef,
                float,
                tolerance=0.001
            )
            plot_S_vs_T(data, mu_Ef_values, plots_dir, palette, available_mu_Ef, tolerance=0.001)

        elif choice == '3':
            mu_Ef_values = get_multiple_values(
                "Enter (μ - E_F) value(s) in eV separated by commas (e.g., 1.000,2.000,3.000): ",
                available_mu_Ef,
                float,
                tolerance=0.001
            )
            plot_sigma_vs_T(data, mu_Ef_values, plots_dir, palette, available_mu_Ef, tolerance=0.001)

        elif choice == '4':
            mu_Ef_values = get_multiple_values(
                "Enter (μ - E_F) value(s) in eV separated by commas (e.g., 1.000,2.000,3.000): ",
                available_mu_Ef,
                float,
                tolerance=0.001
            )
            plot_kappae_vs_T(data, mu_Ef_values, plots_dir, palette, available_mu_Ef, tolerance=0.001)

        elif choice == '5':
            print("Exiting the script. Goodbye!")
            sys.exit(0)

        continue_choice = get_user_choice("Do you want to perform another action? (yes/no): ", ['yes', 'no'])
        print()
        if continue_choice == 'no':
            print("All selected actions have been completed. Exiting the script. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()