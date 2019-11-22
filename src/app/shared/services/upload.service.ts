import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import {
  Brick,
  BrickDimension,
  TypedProperty,
  Term,
  DimensionVariable,
  DataValue,
  Context
 } from 'src/app/shared/models/brick';
import { environment } from 'src/environments/environment';
import { Subject } from 'rxjs';
import { delay, tap } from 'rxjs/operators';
import { isEqual } from 'lodash';

@Injectable({
  providedIn: 'root'
})
export class UploadService {

  // brick builder that will be referenced in all components
  public brickBuilder: Brick = new Brick();
  // templates from server and subject that will pass it to type selector combobox
  public brickTypeTemplates: any[];
  templateSub = new Subject();
  selectedTemplate: any;
  uploadSuccessData: any = null;
  uploadFile: File = null;
  requiredProcess = false;

  constructor(
    private http: HttpClient
  ) {
    // get brick type templates once the user is in /upload
    this.getBrickTypeTemplates();
   }

  getBrickBuilder() {
    return this.brickBuilder;
  }

  getBrickTypeTemplates() {
    this.http.get(`${environment.baseURL}/brick_type_templates`)
      .subscribe((data: any) => {
        // store templates so they only need to be loaded once
        this.brickTypeTemplates = data.results;

        // emit results to types selector component
        this.templateSub.next(this.brickTypeTemplates);
      });
  }

  getTemplateSub() {
    // type selector component subscribes to get templates once they are loaded
    return this.templateSub.asObservable();
  }

  setSelectedTemplate(template) {
    // map template values to brick builder object
    this.selectedTemplate = template.id;
    this.brickBuilder.type = template.text;
    this.brickBuilder.template_id = template.id;
    if (template.process) {
      this.requiredProcess = true;
      this.brickBuilder.process = template.process as Term;
    }

    // map complex objects from template to brick builder
    this.setTemplateDataValues(template.data_vars);
    this.setTemplateDimensions(template.dims);
    this.setTemplateProperties(template.properties);
  }

  // map each data value from template as a new datavalue object belonging to the brick
  setTemplateDataValues(dataVars) {

    // clear brickbuilder datavalues if different template is selected
    this.brickBuilder.dataValues = [];

    dataVars.forEach((dataVar, idx) => {
      // set required to true in constructor
      const dataValue = new DataValue(idx, true);

      // set units to a term if its not empty or else null
      dataValue.units = (this.valuelessUnits(dataVar.units) ? null : dataVar.units) as Term;
      dataValue.type = dataVar.type;
      // dataValue.microType = dataVar.microtype;
      dataValue.scalarType = dataVar.scalar_type as Term;

      // create array of context objects for every data value that has context-
      if (dataVar.context && dataVar.context.length) {
        dataVar.context.forEach(ctx => {
          dataValue.context.push(this.setContext(ctx));
        });
      }

      // add dataValue to brick builder once values are set
      this.brickBuilder.dataValues.push(dataValue);
    });
  }

  setTemplateDimensions(dims) {

    // clear previous dimensions if new template is selected
    this.brickBuilder.dimensions = [];

    dims.forEach((item, idx) => {
      // set required to true in constructor
      const dim = new BrickDimension(this.brickBuilder, idx, true);
      // set dimension type
      dim.type = new Term(item.type.id, item.type.text);

      // create array of dimension variables from template
      item.dim_vars.forEach((dvItem, dvIdx) => {
        const dimVar = new DimensionVariable(dim, dvIdx, true);

        // set units to a term if units object does not contain empty values
        dimVar.units = (this.valuelessUnits(dvItem.units) ? null : dvItem.units) as Term;
        dimVar.type = dvItem.type;
        dimVar.scalarType = dvItem.scalar_type as Term;

        // create array of context objects for every dimension variable that has context
        if (dvItem.context && dvItem.context.length) {
          dvItem.context.forEach(ctx => {
            dimVar.context.push(this.setContext(ctx));
          });
        }
        // add variables to dimension once values are set
        dim.variables.push(dimVar);
      });
      // add dimension to brick once values are set
      this.brickBuilder.dimensions.push(dim);
    });
  }

  setTemplateProperties(props) {
    // clear previous properties if new template is selected
    this.brickBuilder.properties = [];

    props.forEach((item, idx) => {
      // set required to true in constructor
      const prop = new TypedProperty(idx, true);

      // set units to a term if units object does not containe empty values
      prop.units = (this.valuelessUnits(item.units) ? null : item.units) as Term;
      prop.type = item.property as Term;
      prop.value = item.value as Term;
      prop.value = item.property.scalar_type === 'oterm_ref'
        ? prop.value as Term
        : prop.value.text;

      // create array of context objects for every property that has context
      if (item.context && item.context.length) {
        item.context.forEach(ctx => {
          prop.context.push(this.setContext(ctx));
         });
      }
      // add property to brick once values are set
      this.brickBuilder.properties.push(prop);
    });
  }

  setContext(ctx): Context {
    // create new context from template
    const context = new Context();

    //set context properties
    context.required = ctx.required;
    context.type = ctx.property;
    context.value = new Term(ctx.value.id, ctx.value.text);
    if (!this.valuelessUnits(ctx.units)) {
      context.units = new Term(ctx.units.id, ctx.units.text);
    }
    return context;
  }

  valuelessUnits(units) {
    // helper method to find empty term objects
    return isEqual(units, {id: '', text: ''});
  }

  public searchOntTerms(term) {
    // get any ontological terms from database that match term
    return this.http.get(`${environment.baseURL}/search_ont_all/${term}`);
  }

  public searchOntUnits(term) {
    // get any ontological units from database that match term
    return this.http.get(`${environment.baseURL}/search_ont_units/${term}`);
  }

  public searchOntPropertyValues(value: string, microtype: any) {
    const body = { microtype, value };
    return this.http.post<any>(`${environment.baseURL}/search_property_value_oterms`, body).pipe(delay(500));
  }

  public searchOntPropertyUnits(microtype: any) {
    const body = { microtype };
    return this.http.post<any>(`${environment.baseURL}/get_property_units_oterms`, body);
  }

  public searchDataVariableMicroTypes(term) {
    return this.http.get(`${environment.baseURL}/search_data_variable_microtypes/${term}`).pipe(delay(500));
  }

  public searchDimensionMicroTypes(term) {
    return this.http.get(`${environment.baseURL}/search_dimension_microtypes/${term}`).pipe(delay(500));
  }

  public searchDimensionVariableMicroTypes(term) {
    return this.http.get(`${environment.baseURL}/search_dimension_variable_microtypes/${term}`).pipe(delay(500));
  }

  public searchPropertyMicroTypes(term) {
    return this.http.get(`${environment.baseURL}/search_property_microtypes/${term}`).pipe(delay(500));
  }

  public getProcessOterms() {
    return this.http.get(`${environment.baseURL}/get_process_oterms`);
  }

  public getCampaignOterms() {
    return this.http.get(`${environment.baseURL}/get_campaign_oterms`);
  }

  public getPersonnelOterms() {
    return this.http.get(`${environment.baseURL}/get_personnel_oterms`);
  }

  public getValidationResults() {
    const body = { data_id: this.brickBuilder.data_id };
    return this.http.post<any>(`${environment.baseURL}/validate_upload`, body);
  }

  mapDimVarToCoreTypes(dimVar) {
    // mapping dimension variable to core types, still prototyping
    const formData: FormData = new FormData();
    formData.append('brick', this.brickBuilder.toJson());
    formData.append('dimIndex', dimVar.dimension.index);
    formData.append('dimVarIndex', dimVar.index);
    return this.http.post<any>(`${environment.baseURL}/map_dim_variable`, formData);
  }

  uploadBrick(file: File) {
    // method that handles user uploaded excel file in load component
    const formData: FormData = new FormData();

    // add brick and uploaded file to form data
    formData.append('files', file, file.name);
    formData.append('brick', this.brickBuilder.toJson());

    // upload brick to server
    const returnResponse = new Promise((resolve, reject) => {
      this.http.post(`${environment.baseURL}/upload`, formData)
        .subscribe((res: any) => {
          if (res.error) {
            reject(res);
          } else {
            this.mapBrickData(res);
            resolve(res);
          }
        },
          err => {
            reject(err);
          }
        );
    });
    return returnResponse;
  }

  setSuccessData(data: any) {
    this.uploadSuccessData = data;
  }

  setFile(data: File) {
    this.uploadFile = data;
  }

  downloadBrickTemplate() {
    const formData: FormData = new FormData();
    const blobOrJson = this.brickBuilder.isEmpty ? 'json' : 'blob';

    // we need to upload the brick data to get the right download template
    formData.append('brick', this.brickBuilder.toJson());

    // headers and config that will allow user to download .xlsx file format
    const config = {
      headers: new HttpHeaders({
        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }),
      // responseType: 'blob' as 'json'
      responseType: blobOrJson as 'json'
    };

    return new Promise((resolve) => {
      this.http.post<any>(`${environment.baseURL}/generate_brick_template`, formData, config)
        .subscribe(res => {
          if (res.error) {
            // reject(res);
            // throw new Error(res.error);
          } else {
            resolve(res);
          }
        });
    });
  }

  mapBrickData(res: any) {

    // Method that maps upload results to brick
    this.brickBuilder.data_id = res.results.data_id;

    // set size and data for each dimension
    this.brickBuilder.dimensions.forEach((dim, idx) => {
      const dimData = res.results.dims[idx];
      dim.size = dimData.size;

      // set value sample of variables for each dimension variable
      dim.variables.forEach((dimVar, dvIdx) => {
        dimVar.valuesSample = dimData.dim_vars[dvIdx].value_example;
      });
    });

    // set data and value sample for each brick data value
    this.brickBuilder.dataValues.forEach((val, idx) => {
      const valueData = res.results.data_vars[idx];
      val.valuesSample = valueData.value_example;
    });
  }

  submitBrick() {
    // final step in uploading brick after everything is validated
    const formData: FormData = new FormData();
    formData.append('brick', this.brickBuilder.toJson());
    return this.http.post<any>(`${environment.baseURL}/create_brick`, formData);
  }

}
