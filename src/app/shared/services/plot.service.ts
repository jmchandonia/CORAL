import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyBuilder } from 'src/app/shared/models/plotly-builder';
@Injectable({
  providedIn: 'root'
})
export class PlotService {

  public plot: PlotlyBuilder;
  // public plotBuilder: PlotBuilder = new PlotBuilder();
  // public plotType: string;
  // metadata: ObjectMetadata;

  constructor(private http: HttpClient) { }

  getPlotlyBuilder(coreType?, query?: QueryBuilder) {
    if (!this.plot) {
      this.plot = JSON.parse(localStorage.getItem('plotlyBuilder')) || new PlotlyBuilder(coreType, query);
    }
    return this.plot;
  }

  deletePlotBuilder() {
    localStorage.removeItem('plotlyBuilder');
    delete this.plot;
  }

  getPlotlyResult() {
    return this.http.post<any>(`${environment.baseURL}/plotly_data`, this.getPlotlyBuilder());
  }

  getPlotTypes() {
    return this.http.get(`${environment.baseURL}/plot_types`);
  }

  getReportPlotData(id) {
    // method used to get data for dashboard component
    return this.http.get(`${environment.baseURL}/report_plot_data/${id}`);
  }

  getCoreTypeMetadata() {
    return this.http.get(environment.baseURL + '/plot_core_type_metadata');
  }

}
