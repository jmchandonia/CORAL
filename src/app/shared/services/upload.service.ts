import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import {
  Brick,
  BrickDimension,
  TypedProperty,
  Term,
  DimensionVariable,
  DataValue
 } from 'src/app/shared/models/brick';
import { environment } from 'src/environments/environment';
import { Subject } from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class UploadService {

  public brickBuilder: Brick = new Brick();
  public brickTypeTemplates: any[];
  templateSub = new Subject();
  selectedTemplate: any;

  getBrickBuilder() {
    return this.brickBuilder;
  }

  testBrickBuilder() {
    console.log('CURRENT BRICK OBJECT', this.brickBuilder);
  }

  constructor(
    private http: HttpClient
  ) {
    this.getBrickTypeTemplates();
   }

  getDataTypes() {
    return this.http.get(`${environment.baseURL}/data_types`);
  }

  getBrickTypeTemplates() {
    // return this.http.get(`${environment.baseURL}/brick_type_templates`);
    this.http.get(`${environment.baseURL}/brick_type_templates`)
      .subscribe((data: any) => {
        this.brickTypeTemplates = data.results;
        this.templateSub.next(this.brickTypeTemplates);
      });
  }

  getTemplateSub() {
    return this.templateSub.asObservable();
  }

  setSelectedTemplate(template) {
    this.selectedTemplate = template.id;
    this.brickBuilder.type = template.text;
    this.brickBuilder.template_id = template.id;
    this.brickBuilder.name = template.text;
    this.setTemplateDataValues(template.data_vars);
    this.setTemplateDimensions(template.dims);
    this.setTemplateProperties(template.properties);
  }

  setTemplateDataValues(dataVars) {
    this.brickBuilder.dataValues = [];
    dataVars.forEach((dataVar, idx) => {
      const dataValue = new DataValue(idx, true);
      dataValue.type = dataVar.type as Term;
      dataValue.units = dataVar.units as Term;
      dataValue.scalarType = dataVar.scalar_type as Term;
      this.brickBuilder.dataValues.push(dataValue);
    });
  }

  setTemplateDimensions(dims) {
    this.brickBuilder.dimensions = [];
    dims.forEach((item, idx) => {
      const dim = new BrickDimension(this.brickBuilder, idx, true);
      dim.type = new Term(item.type.id, item.type.text);
      item.dim_vars.forEach((dvItem, dvIdx) => {
        const dimVar = new DimensionVariable(this.brickBuilder, dvIdx, true);
        dimVar.type = dvItem.type as Term;
        dimVar.scalarType = dvItem.scalar_type as Term;
        dimVar.units = dvItem.units as Term;
        dim.variables.push(dimVar);
      });
      this.brickBuilder.dimensions.push(dim);
    });
  }

  setTemplateProperties(props) {
    this.brickBuilder.properties = [];
    props.forEach((item, idx) => {
      const prop = new TypedProperty(idx, true);
      prop.type = item.property as Term;
      prop.units = item.units as Term;
      prop.value = item.value as Term;
      this.brickBuilder.properties.push(prop);
    });
  }

  getDataModels() {
    return this.http.get(`${environment.baseURL}/data_models`);
  }

  public searchOntTerms(term) {
    return this.http.get(`${environment.baseURL}/search_ont_all/${term}`);
  }

  public searchOntUnits(term) {
    return this.http.get(`${environment.baseURL}/search_ont_units/${term}`);
  }

  uploadBrick(file: File) {
    const formData: FormData = new FormData();
    formData.append('files', file, file.name);
    formData.append('brick', this.brickBuilder.toJson());
    const returnResponse = new Promise((resolve, reject) => {
      this.http.post(`${environment.baseURL}/upload`, formData)
        .subscribe((res: any) => {
          this.mapBrickData(res);
          resolve(res);
        },
          err => {
            reject(err);
          }
        );
    });
    return returnResponse;
  }

  downloadBrickTemplate() {
    const formData: FormData = new FormData();
    formData.append('brick', this.brickBuilder.toJson());
    const config = {
      headers: new HttpHeaders({
        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }),
      responseType: 'blob' as 'json'
    };
    return this.http.post<any>(`${environment.baseURL}/generate_brick_template`, formData, config);
  }

  mapBrickData(res: any) {
    this.brickBuilder.data_id = res.results.data_id;
    this.brickBuilder.dimensions.forEach((dim, idx) => {
      const dimData = res.results.dims[idx];
      dim.size = dimData.size;
      dim.variables.map((dimVar, dvIdx) => {
        dimVar.valuesSample = dimData.dim_vars[dvIdx].value_example;
      });
    });
    this.brickBuilder.dataValues.forEach((val, idx) => {
      const valueData = res.results.data_vars[idx];
      val.valuesSample = valueData.value_example;
    });
  }

}
