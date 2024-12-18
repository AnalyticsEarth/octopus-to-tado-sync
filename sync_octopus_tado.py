import argparse
import requests
from requests.auth import HTTPBasicAuth
from PyTado.interface import Tado
from datetime import datetime


def get_meter_reading_total_consumption(api_key, mprn, gas_serial_number):
    """
    Retrieves total gas consumption from the Octopus Energy API for the given gas meter point and serial number.
    """
    url = f"https://api.octopus.energy/v1/gas-meter-points/{mprn}/meters/{gas_serial_number}/consumption/?group_by=quarter"
    total_consumption = 0.0
    max_date = datetime.min

    while url:
        response = requests.get(
            url, auth=HTTPBasicAuth(api_key, "")
        )

        if response.status_code == 200:
            meter_readings = response.json()
            print(meter_readings)
            max_date = max(max_date,max(
                datetime.strptime(interval["interval_end"],'%Y-%m-%dT%H:%M:%SZ') for interval in meter_readings["results"]
            ))
            total_consumption += sum(
                interval["consumption"] for interval in meter_readings["results"]
            )
            url = meter_readings.get("next", "")
        else:
            print(
                f"Failed to retrieve data. Status code: {response.status_code}, Message: {response.text}"
            )
            break

    print(f"Latest Date is {max_date}")
    print(f"Total consumption is {total_consumption}")
    return max_date, total_consumption


def send_reading_to_tado(username, password, reading):
    """
    Sends the total consumption reading to Tado using its Energy IQ feature.
    """
    tado = Tado(username, password)
    print(reading)
    max_date = reading[0].date().strftime('%Y-%m-%d')
    consumption = int(reading[1])
    print(max_date)
    print(consumption)
    result = tado.set_eiq_meter_readings(date=max_date, reading=consumption)
    print(result)


def parse_args():
    """
    Parses command-line arguments for Tado and Octopus API credentials and meter details.
    """
    parser = argparse.ArgumentParser(
        description="Tado and Octopus API Interaction Script"
    )

    # Tado API arguments
    parser.add_argument("--tado-email", required=True, help="Tado account email")
    parser.add_argument("--tado-password", required=True, help="Tado account password")

    # Octopus API arguments
    parser.add_argument(
        "--mprn",
        required=True,
        help="MPRN (Meter Point Reference Number) for the gas meter",
    )
    parser.add_argument(
        "--gas-serial-number", required=True, help="Gas meter serial number"
    )
    parser.add_argument("--octopus-api-key", required=True, help="Octopus API key")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Get total consumption from Octopus Energy API
    consumption = get_meter_reading_total_consumption(
        args.octopus_api_key, args.mprn, args.gas_serial_number
    )

    # Send the total consumption to Tado
    send_reading_to_tado(args.tado_email, args.tado_password, consumption)
