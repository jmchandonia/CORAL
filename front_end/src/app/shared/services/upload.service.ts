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
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';

@Injectable({
  providedIn: 'root'
})
export class UploadService {

  // brick builder that will be referenced in all components
  public brickBuilder: Brick;
  // templates from server and subject that will pass it to type selector combobox
  public brickTypeTemplates: any[];
  templateSub = new Subject();
  selectedTemplate: any;
  uploadSuccessData: any = null;
  uploadFile: File = null;
  requiredProcess = false;

  constructor(
    private http: HttpClient,
  ) {
    // get brick type templates once the user is in /upload
    this.getBrickTypeTemplates();
   }

  getBrickBuilder() {
    if (this.brickBuilder) {
      return this.brickBuilder;
    } else {
      const localStorageBrick = JSON.parse(localStorage.getItem('brickBuilder'));
      if (localStorageBrick !== null) {
        this.brickBuilder = BrickFactoryService.createUploadInstanceFromLS(localStorageBrick);
        return this.brickBuilder;
      }
    }
  }

  saveBrickBuilder() {
    localStorage.setItem('brickBuilder', this.brickBuilder.toJson());
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
    delete this.brickBuilder;
    this.brickBuilder = BrickFactoryService.createUploadInstance(template);
    this.selectedTemplate = template.id;
    localStorage.setItem('selectedTemplate', this.selectedTemplate);
    this.saveBrickBuilder();
  }

  getSelectedTemplate() {
    if (!this.selectedTemplate) {
      return localStorage.getItem('selectedTemplate');
    } else {
      return this.selectedTemplate;
    }
  }

  clearCache() {
    // this.brickBuilder = new Brick();
    delete this.brickBuilder;
    localStorage.removeItem('brickBuilder');
    localStorage.removeItem('selectedTemplate');
    this.uploadFile = null;
    this.uploadSuccessData = null;
    delete this.selectedTemplate;
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

  // method to be used for microtype browser component
  public getMicroTypes() {
    return this.http.get(`${environment.baseURL}/microtypes`);
  }

  public searchOntPropertyValues(value: string, microtype: any) {
    const body = { microtype, value };
    return this.http.post<any>(`${environment.baseURL}/search_property_value_oterms`, body).pipe(delay(500));
  }

  // tslint:disable-next-line
  public searchPropertyValueObjectRefs(value: string, term_id: string, microtype: any) {
    const body = { value, microtype, term_id };
    return this.http.post<any>(`${environment.baseURL}/search_property_value_objrefs`, body).pipe(delay(500));
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

  public getDataVarValidationErrors(idx) {
    return this.http.get(`${environment.baseURL}/data_var_validation_errors/${this.brickBuilder.data_id}/${idx}`);
  }

  public getDimVarValidationErrors(idx, dvIdx) {
    return this.http.get(`${environment.baseURL}/dim_var_validation_errors/${this.brickBuilder.data_id}/${idx}/${dvIdx}`);
  }

  public getValidationResults() {
    const body = { data_id: this.brickBuilder.data_id };
    return this.http.post<any>(`${environment.baseURL}/validate_upload`, body);
  }

  public getRefsToCoreObjects() {
    const formData: FormData = new FormData();
    formData.append('brick', this.brickBuilder.toJson());
    return this.http.post<any>(`${environment.baseURL}/refs_to_core_objects`, formData);
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

    // we need to upload the brick data to get the right download template
    formData.append('brick', this.brickBuilder.toJson());

    // headers and config that will allow user to download .xlsx file format
    const config = {
      headers: new HttpHeaders({
        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }),
      responseType: 'blob' as 'json'
    };

    return new Promise((resolve) => {
      this.http.post<any>(`${environment.baseURL}/generate_brick_template`, formData, config)
        .subscribe(res => {
          if (res.type === 'text/html') {
            // TODO: figure out a way to have a responseType of both JSON and blob in order to read errors sent from server
            res.text().then(console.error);
            throw new Error('We\'re sorry, but something went wrong with the file type that you have currently uploaded');
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
        dimVar.totalCount = dim.size;
      });
    });

    // set data and value sample for each brick data value
    this.brickBuilder.dataValues.forEach((val, idx) => {
      const valueData = res.results.data_vars[idx];
      val.valuesSample = valueData.value_example;
      val.totalCount = valueData.size;
    });
  }

  submitBrick() {
    // final step in uploading brick after everything is validated
    const formData: FormData = new FormData();
    formData.append('brick', this.brickBuilder.toJson());
    return this.http.post<any>(`${environment.baseURL}/create_brick`, formData);
  }

}
