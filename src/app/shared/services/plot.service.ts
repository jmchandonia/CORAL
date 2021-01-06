import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyBuilder, Constraint, AxisOption } from 'src/app/shared/models/plotly-builder';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { map, delay } from 'rxjs/operators';
import { Response } from 'src/app/shared/models/response';
import { ObjectMetadata } from 'src/app/shared/models/object-metadata';
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

  getObjectPlotMetadata(id: string) {
    return this.http.get<ObjectMetadata>(`${environment.baseURL}/brick_plot_metadata/${id}/100`)
      .pipe(map(data => {
        return {
          result: data,
          axisOptions: PlotService.mapBrickPropertiesToAxisOptions(data)
        }
      }))
  }

  getBrickDimVarValues(id: string, dimIdx: number, dvIdx: number, keyword: string) {
    return this.http.get(`${environment.baseURL}/brick_dim_var_values/${id}/${dimIdx}/${dvIdx}/${keyword}`).pipe(delay(500));
  }

  getStaticMap(mapBuilder: MapBuilder) {
    return this.http.post<any>(`${environment.baseURL}/search`, mapBuilder.query)
      .pipe(
        map(({data}) => {
          return data.map(item => ({
            ...item,
            color: item[mapBuilder.colorField.name],
            label_text: item[mapBuilder.labelField.name]}
          ));
        })
      );
  }

  public static mapBrickPropertiesToAxisOptions(data: ObjectMetadata): AxisOption[] {
    const axisOptions: AxisOption[] = [];
    data.dim_context.forEach((dim, i) => {
      dim.typed_values.forEach((dimVar, j) => {
        axisOptions.push({
          scalar_type: dimVar.values.scalar_type,
          name: dimVar.value_no_units,
          display_name: dimVar.value_with_units,
          term_id: dimVar.value_type.oterm_ref,
          dimension: i,
          dimension_variable: j,
          units: dimVar.value_units
        });
      });
    });
    data.typed_values.forEach((dataVar, i) => {
      axisOptions.push({
        scalar_type: dataVar.values.scalar_type,
        name: dataVar.value_no_units,
        display_name: dataVar.value_with_units,
        term_id: dataVar.value_type.oterm_ref,
        data_variable: i,
        units: dataVar.value_units
      });
    });
    return axisOptions;
  }

  testDynamicMap(id: string, mapBuilder: MapBuilder) {
    return this.http.post(`${environment.baseURL}/filter_brick/${id}`, mapBuilder.createPostData())
      .pipe(map((data: any) => {
        const response = data.res[0];
        return Array(response.x.length)
          .fill(null)
          .map((_, i) => ({
            latitude: response.x[i],
            longitude: response.y[i],
            color: response.z[i],
            label_text: response['point-labels'][i],
            hover: false
          }))
      }))
  }

  getDynamicPlot(plot: PlotlyBuilder) {
    const data = plot.urlPostData !== undefined ? plot.urlPostData : plot.createPostData();
    return this.http.post(`${environment.baseURL}/filter_brick/${plot.object_id}`, data);
  }

  testPlotlyResult(id: string) {
    return this.http.post(`${environment.baseURL}/filter_brick/${id}`, {
      'constant': {'2/1': 5, '2/4': 2, '3': 1},
      'variable': ['1/1', '2/2', '2/3']
    });
  }
}
