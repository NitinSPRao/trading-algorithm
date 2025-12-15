def annualized_return(starting_fund, final_fund, start_date, end_date):
    """
    Calculate the annualized return of an investment.

    Parameters:
    starting_fund (float): The initial amount of money invested.
    final_fund (float): The amount of money at the end of the investment period.
    start_date (str): The start date of the investment period in 'YYYY-MM-DD' format.
    end_date (str): The end date of the investment period in 'YYYY-MM-DD' format.

    Returns:
    float: The annualized return as a percentage.
    """
    from datetime import datetime

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    years = (end_date - start_date).days / 365.25

    return_value = (final_fund / starting_fund) ** (1 / years) - 1

    return return_value * 100


if __name__ == "__main__":
    starting_fund = 10000
    final_fund = 5850796
    start_date = "2008-12-17"
    end_date = "2025-02-21"

    annualized_return_value = annualized_return(starting_fund, final_fund, start_date, end_date)
    print(f"The annualized return is: {annualized_return_value:.2f}%")
