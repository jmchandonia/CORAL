import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyBuilder, Constraint } from 'src/app/shared/models/plotly-builder';
@Injectable({
  providedIn: 'root'
})
export class PlotService {

  public plot: PlotlyBuilder;

  constructor(private http: HttpClient) { }

  getPlotlyBuilder(coreType?, query?: QueryBuilder) {
    if (!this.plot) {
      // needs object.assign to have class methods
      this.plot = Object.assign(
        new PlotlyBuilder(coreType, query),
        JSON.parse(localStorage.getItem('plotlyBuilder'))
      );
    }
    return this.plot;
  }

  deletePlotBuilder() {
    localStorage.removeItem('mapBuilder');
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
