package org.eqasim.odyssee;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.util.List;

public class ScalableRoutingResultWriter {
	private final File output;

	public ScalableRoutingResultWriter(String path) throws IOException {
		this.output = new File(path);
		BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(this.output)));
		writer.write(String.join(";", new String[] { //
				"person_id", //
				"office_id", //
				"car_travel_time", //
				"car_distance", //
				"pt_travel_time", //
				"pt_distance" //
		}) + "\n");
		writer.close();
	}

	public void write(List<RoutingResult> results) throws IOException {
		BufferedWriter writer = new BufferedWriter(new FileWriter(this.output, true));

		for (RoutingResult result : results) {
			writer.write(String.join(";", new String[] { //
					result.personId, //
					result.officeId, //
					String.valueOf(result.carTravelTime), //
					String.valueOf(result.carDistance), //
					String.valueOf(result.ptTravelTime), //
					String.valueOf(result.ptDistance), //
			}) + "\n");
		}
		writer.close();
	}
}
