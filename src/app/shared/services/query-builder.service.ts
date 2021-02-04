import { Injectable } from '@angular/core';
import { QueryBuilder } from '../models/QueryBuilder';
import { Subject } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
@Injectable({
  providedIn: 'root'
})
export class QueryBuilderService {

  public queryBuilderObject: QueryBuilder = new QueryBuilder();
  // public queryBuilderSub = new Subject<QueryBuilder>();
  dataTypeSub: Subject<any> = new Subject();
  searchType: string;
  dataTypes: any[];
  dataModels: any[];
  operators: any[];
  dataTypeHash: any = {};
  previousUrl: string;

  constructor(
    private http: HttpClient,
    private router: Router,
    private santitizer: DomSanitizer
  ) { }

  getDataTypesandModels() {
    this.http.get(`${environment.baseURL}/data_models`)
    .subscribe((models: any) => {
      this.dataModels = models.results;
      this.http.get(`${environment.baseURL}/data_types`)
      .subscribe((types: any) => {
        this.dataTypes = types.results;
        this.dataTypeSub.next(this.dataTypes);
        this.dataTypes.forEach((dataType: any) => {
          const dataModel = this.dataModels[dataType.dataModel];
          this.dataTypeHash[dataType.dataType] = dataModel.properties;
        });
      });
    });
    this.http.get(`${environment.baseURL}/search_operations`)
      .subscribe((operations: any) => {
        this.operators = operations.results;
      });
  }

  getQueryBuilderCache() {
    return JSON.parse(localStorage.getItem('queryBuilder'));
  }

  setQueryBuilderCache() {
    localStorage.setItem('queryBuilder', JSON.stringify(this.queryBuilderObject));
  }

  setPreviousUrl(url) {
    this.previousUrl = url;
  }

  getPreviousUrl() {
    return this.previousUrl;
  }

  getLoadedDataTypes() {
    return this.dataTypes;
  }

  getCurrentObject() {
    return this.queryBuilderObject;
  }

  resetObject() {
    this.queryBuilderObject = new QueryBuilder();
  }

  validSearchQuery() {
    return this.queryBuilderObject.isValid;
  }

  getSearchResults(format = 'JSON') {
    if (this.queryBuilderObject.isEmpty) {
      this.queryBuilderObject = this.getQueryBuilderCache();
    }
    return this.http.post<any>(`${environment.baseURL}/search`, {...this.queryBuilderObject, format}, {
      responseType: format === 'TSV' ? 'arraybuffer' as 'json' : 'json'
    });
  }

  downloadCoreType(id: string) {
    return this.http.post<any>(`${environment.baseURL}/core_type_metadata/${id}`, {format: 'TSV'});
  }

  downloadBrick(id: string, format: string) {
    return this.http.post<any>(`${environment.baseURL}/brick/${id}`, {format});
  }

  getObjectMetadata(id) {
    return this.http.get(`${environment.baseURL}/brick_metadata/${id}`);
  }

  getCoreTypeMetadata(id) {
    return this.http.get(`${environment.baseURL}/core_type_metadata/${id}`);
  }

  getCoreTypeProps(name: string) {
    return this.http.get(`${environment.baseURL}/core_type_props/${name}`)
  }

  getDimensionVariableValues(id: string, dimIdx: number) {
    return this.http.get(`${environment.baseURL}/brick_dimension/${id}/${dimIdx}`);
  }

  getDataTypes() {
    return this.dataTypeSub.asObservable();
  }

  getAttributes(dataType) {
    return this.dataTypeHash[dataType];
  }

  getDataTypeValue(value) {
    return;
  }

  getDataModels() {
    return this.http.get(`${environment.baseURL}/data_models`);
  }

  getOperators() {
    return this.operators;
  }

  getOperatorValue(item) {
    const index = this.operators.indexOf(item);
    if (index >= 0) {
      return index.toString();
    }
  }

  getSearchType() {
    return this.searchType;
  }

  getProcessesUp(id) {
    return this.http.get(`${environment.baseURL}/up_process_docs/${id}`);
  }

  getProcessesDown(id) {
    return this.http.get(`${environment.baseURL}/dn_process_docs/${id}`);
  }

  setSearchType(searchType: string) {
    this.searchType = searchType;
  }

  getProcessOterms() {
    return this.http.get(`${environment.baseURL}/get_process_oterms`);
  }

  getCampaignOterms(): Observable<any> {
    return this.http.get<any>(`${environment.baseURL}/get_campaign_oterms`);
  }

  getPersonnelOterms() {
    return this.http.get(`${environment.baseURL}/get_personnel_oterms`);
  }

  getImageSrc(url): Promise<SafeUrl> {
    return new Promise((resolve, reject) => {
      this.http.post(`${environment.baseURL}/image`, {url})
        .subscribe((response: any) => {
          resolve(this.santitizer.bypassSecurityTrustUrl('data:image/jpeg;base64,' + response.results.image))
        });
    });
  }

  getMapSearchResults(query: QueryBuilder) {
    return this.http.post<any>(`${environment.baseURL}/search`, query);
  }


}
