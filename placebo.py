from random import randrange, choice
from datetime import datetime, timedelta
from argparse import ArgumentParser
from itertools import groupby
from calendar import monthrange


def generate_plan_seq_randomized(
        duration=120,
        interval_min=3,
        interval_max=4,
        treatments=None):
    """
    generate a sequence of treatments for a trial.

    returns a sequence of treatments chosen from a list of options.
    treatment interval length is randomized within the specified bounds.
    each new treatment interval is randomized, so treatments may repeat.

    Args:
        duration: number of plan units to generate
        interval_min: minimum duration of an interval of the same treatment
        interval_max: maximum duration of an interval of the same treatment
        treatments: seq of treatment options. default: ["placebo","treatment"]
    """
    assert interval_max >= interval_min
    if treatments is None:
        treatments =["placebo","treatment"]
    plan = []
    while len(plan) < duration:
        # generate a treatment interval
        if interval_min == interval_max:
            interval = interval_min
        else:
            interval = randrange(interval_min, interval_max+1)
        # generate a choice of treatment
        treatment = choice(treatments)
        # add the new treatment interval to the plan
        plan.extend([treatment] * interval)
    plan = plan[:duration] # cut off any extra past desired duration
    return plan


def generate_plan_seq_binary_crossover(
        duration=120,
        interval_min=4,
        interval_max=5,
        treatments=None):
    """
    generate a sequence of treatments for a binary-crossover trial.

    returns a sequence of treatments crossing over between two options.
    treatment interval length is randomized within the specified bounds.

    Args:
        duration: number of plan units to generate
        interval_min: minimum duration of an interval of the same treatment
        interval_max: maximum duration of an interval of the same treatment
        treatments: seq of 2 treatment options. default: ["placebo","treatment"]
    """
    assert interval_max >= interval_min
    if treatments is None:
        treatments =["placebo","treatment"]
    assert len(treatments) == 2 # must be only two treatment options
    plan = []
    # generate a choice of initial treatment
    treatment_index = choice([0,1])
    def not_gate(x):
        return 1 if x == 0 else 0
    while len(plan) < duration:
        # generate a treatment interval length
        if interval_min == interval_max:
            interval = interval_min
        else:
            interval = randrange(interval_min, interval_max+1)
        # swap treatments from the last
        treatment_index = not_gate(treatment_index)
        # add new treatment interval to the plan sequence
        plan.extend([treatments[treatment_index]] * interval)
    plan = plan[:duration] # cut off any extra past desired duration
    return plan


def enumerate_seq(s, use_date=True, start_date="2025-01-01"):
    """
    turn a sequence of strings into an enumerated or dated string w/ newlines

    Args:
        s: sequence of strings
        use_date: whether to output a dated or just an enumerated list
        start_date: start date if the output is dated
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    if not use_date: # if no date, just enumerate
        return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(s))
    # if date, generate sequential dates for each item
    def date_item(date, d, item):
        return f"{(date + timedelta(days=d)).strftime('%Y-%m-%d')}: {item}"
    return '\n'.join(date_item(start, i, item) for i, item in enumerate(s))


def grid_dated_strings(dated_strings):
    """
    format a list of dated strings into a monthly pill-organizer grid

    to make it easy to prepare doses for a trial.
    mostly by claude.
    
    Args:
        dated_strings: seq of dates and strings in format "date: string"
    """
    # Split each string into date and value
    data = [s.split(': ') for s in dated_strings.splitlines()]
    # Convert dates to datetime objects
    data = [(datetime.strptime(date, '%Y-%m-%d'), value)
        for date, value in data]
    # Group data by month
    grouped_data = [list(g) for _, g in groupby(data,
        key=lambda x: x[0].strftime('%Y-%m'))]

    # Format each month
    formatted_months = []
    for month_data in grouped_data:
        # Get the month name and the number of days in the month
        month_name = month_data[0][0].strftime('%B %Y')
        _, n_days = monthrange(month_data[0][0].year, month_data[0][0].month)

        # Create a dictionary to store the values for each day
        month_dict = {d.day: v for d, v in month_data}

        # Generate the grid rows
        rows = [range(1, 9), range(9, 17), range(17, 25), range(25, n_days + 1)]

        # Format each row
        formatted_rows = []
        for row in rows:
            # Extract dates and values
            dates = [d for d in row if d <= n_days]
            values = [month_dict.get(d, '') for d in dates]
            # Format dates and values
            formatted_dates = ' '.join(str(d).rjust(2) for d in dates)
            formatted_values = ' '.join(v.ljust(10) for v in values)
            # Pad the last row with spaces to match the length of the other rows
            if row == rows[-1]:
                padding_dates = ' '.join('  ' for _ in range(8 - len(dates)))
                padding_values = ' '.join(' ' * 10 for _ in range(8 - len(dates)))
                formatted_row = (f"{formatted_dates} {padding_dates}"
                    f"  {formatted_values} {padding_values}")
            else:
                formatted_row = f"{formatted_dates}  {formatted_values}"

            formatted_rows.append(formatted_row)

        # Join rows into a single string for the month, preceded by month name
        formatted_month = f"{month_name}\n" + '\n'.join(formatted_rows)
        formatted_months.append(formatted_month)

    # Join months into a single string, separated by a blank line
    return '\n\n'.join(formatted_months)

# generate a treatment seq, enumerate it by date and write a gridded text file
if __name__ == '__main__':
    parser = ArgumentParser(
        description='write a file containing a binary crossover treatment plan')

    # Add arguments here. For example:
    parser.add_argument('--duration',
        type=int,
        default=120,
        help='Duration of treatment plan in days')
    parser.add_argument('--interval_min',
        type=int,
        default=4,
        help='minimum length of treatment/placebo interval')
    parser.add_argument('--interval_max',
        type=int,
        default=5,
        help='maximum length of treatment/placebo interval')
    parser.add_argument('--start_date',
        type=str,
        default="2025-01-01",
        help='start date of treatment plan in ISO 8601, e.g. 2025-01-01')
    parser.add_argument('--output_file_path',
        type=str,
        default="output.txt",
        help='path to output file')
    args = parser.parse_args()

    seq = generate_plan_seq_binary_crossover(
        duration=args.duration,
        interval_min=args.interval_min,
        interval_max=args.interval_max)
    # pylint: disable=C0103
    dated_list = enumerate_seq(seq, start_date=args.start_date)
    gridded_dates = grid_dated_strings(dated_list)

    with open(args.output_file_path, 'w', encoding="utf-8") as f:
        f.write(gridded_dates + '\n\n' + dated_list)
