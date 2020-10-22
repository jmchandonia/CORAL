import { Injectable } from '@angular/core';
import { PlotBuilder, Dimension, Config } from '../models/plot-builder';
import { HttpClient } from '@angular/common/http';
import { ObjectMetadata, DimensionContext, TypedValue } from 'src/app/shared/models/object-metadata';
import { environment } from 'src/environments/environment';
import { PlotlyConfig } from 'src/app/shared/models/plotly-config';
import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { CoreTypePlotBuilder } from 'src/app/shared/models/core-type-plot-builder';
@Injectable({
  providedIn: 'root'
})
export class PlotService {

  public plotBuilder: PlotBuilder = new PlotBuilder();
  public plotType: string;
  metadata: ObjectMetadata;

  constructor(private http: HttpClient) {
    const cachedPlotBuilder = this.getPlotCache();
    this.plotBuilder = cachedPlotBuilder ? cachedPlotBuilder : new PlotBuilder();
  }

  getPlotBuilder() {
    return this.plotBuilder;
  }

  getPlotType() {
    return JSON.parse(localStorage.getItem('plotType'));
  }

  setPlotType(value: PlotlyConfig) {
    localStorage.setItem('plotType', JSON.stringify(value));
  }

  setPlotCache() {
    localStorage.setItem('plotBuilder', JSON.stringify(this.plotBuilder));
  }

  getPlotCache() {
    return JSON.parse(localStorage.getItem('plotBuilder'));
  }

  getConfiguredDimensions() {
    const keys = Object.keys(this.plotBuilder.config);
    // return all refenences to dimensions without adding config.title
    return keys.map(v => this.plotBuilder.config[v]).filter(t => typeof t !== 'string');
  }

  getDimDropdownValue(axis: string) {
    return this.plotBuilder.data[axis].toString();
  }

  setConfig(
    metadata: ObjectMetadata,
    callback: (dims: Dimension[]) => void
    ) {
    const { config } = this.plotBuilder;
    const length = metadata.dim_context.length;
    const dim_context: DimensionContext[] = metadata.dim_context;
    const typed_values: TypedValue[] = metadata.typed_values;

    config.title = metadata.data_type.oterm_name + ` (${this.plotBuilder.objectId})`;
    config.x = new Dimension(dim_context, typed_values);
    config.y = new Dimension(dim_context, typed_values);
    if (length > 1) {
      config.z = new Dimension(dim_context, typed_values);
      this.plotBuilder.data.z = '' as any;
      callback([config.x, config.y, config.z]); // add 3 dimensions to form
    } else {
      callback([config.x, config.y]); // add 2 dimensions to form
    }
    this.setPlotCache();
  }

  clearPlotBuilder() {
    localStorage.removeItem('plotType');
    localStorage.removeItem('plotBuilder');
    this.plotBuilder = new PlotBuilder();
  }

  setPlotlyDataAxis(key: string, value: string) {
    this.plotBuilder.data[key] = value;
  }

  getCorePlotlyData(plotBuilder: CoreTypePlotBuilder) {
    return this.http.post<any>(`${environment.baseURL}/plotly_core_data`, plotBuilder);
  }

  getPlotlyData() {
    this.parseIntDataAxes();
    return this.http.post<any>(`${environment.baseURL}/plotly_data`, this.plotBuilder);
  }

  parseIntDataAxes() {
    Object.keys(this.plotBuilder.data).forEach(key => {
      if (this.plotBuilder.data[key] !== 'D') {
        this.plotBuilder.data[key] = parseInt(this.plotBuilder.data[key], 10);
      }
    });
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
