# statistics

1. Query

Parameters: idn: int, float, or str.
				Target value to query.
			item: str, or list.
				The item you want to print.
			dataframe: dataframe, default df
				Name of dataframe.
			col: str, default 'id'.
				In which column to select the raws with the value you assigned in 'idn'.

Returns:	Dataframe.


2. FreqTable

Parameters: dataframe: dataframe.
				Name of dataframe.
			col: str.
				The variable you want to get frequency table.
			sort: int, default 1.
				Three types of sorting, named with interger 1 to 3.
				Type 1 is sorting table by col values.
				Type 2 is sorting table by frequencies.
				Type 3 is sorting table by percentages.
			weightList: list, default [].
				Weight by certain weights.
			wRound: bool, default False.
				Whether to round the weighted frequencies.

Returns:	Dataframe.

