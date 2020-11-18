import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyBuilder, Constraint } from 'src/app/shared/models/plotly-builder';
import { MapBuilder } from 'src/app/shared/models/map-builder';
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

  getCorePlot() {
    return this.http.post(`${environment.baseURL}/plotly_core_data`, this.getPlotlyBuilder());
  }

  getDynamicMap(mapBuilder: MapBuilder) {
    return this.http.post(`${environment.baseURL}/brick_map/${mapBuilder.brickId}`, mapBuilder);
  }

  getDynamicPlot(id: string) {
    const plot = this.getPlotlyBuilder();
    const variable = [`${plot.axes.x.dim_idx + 1}/1`];
    const constant = {};
    plot.constraints.forEach(constraint => {
      const dim_idx = constraint.dim_idx + 1;
      constraint.variables.forEach(dimVar => {
        const dim_var_idx = dimVar.dim_var_idx + 1;
        if (dimVar.type === 'flatten') {
          if (constraint.variables.length === 1) {
            constant[`${dim_idx}`] = dimVar.selected_value + 1;
          } else {
            constant[`${dim_idx}/${dim_var_idx}`] = dimVar.selected_value + 1;
          }
        } else if (dimVar.type === 'series') {
          variable.push(`${dim_idx}/${dim_var_idx}`);
        }
      });
    });
    return this.http.post(`${environment.baseURL}/filter_brick/${id}`, {constant, variable});
  }

  testPlotlyResult(id: string) {
    return this.http.post(`${environment.baseURL}/filter_brick/${id}`, {
      'constant': {'2/1': 5, '2/4': 2, '3': 1},
      'variable': ['1/1', '2/2', '2/3']
    });
  }
}
