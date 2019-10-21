import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Brick,
  BrickDimension,
  TypedProperty,
  Term,
  DimensionVariable
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
    this.setTemplateDimensions(template.dims);
    this.setTemplateProperties(template.properties);
  }

  setTemplateDimensions(dims) {
    this.brickBuilder.dimensions = [];
    dims.forEach((item, idx) => {
      const dim = new BrickDimension(this.brickBuilder, idx, false);
      dim.type = new Term(item.type.id, item.type.text);
      item.dim_vars.forEach((dvItem, dvIdx) => {
        const dimVar = new DimensionVariable(this.brickBuilder, dvIdx);
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
      const prop = new TypedProperty(idx, false);
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
}
