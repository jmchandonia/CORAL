import { Injectable } from '@angular/core';
import { QueryBuilder, QueryMatch, QueryParam } from '../models/QueryBuilder';
import { Subject } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
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

  getMetaData() {

  }

  // getOperators() {

  // }

  getPropertiesFromMetaData() {

  }

  constructor(private http: HttpClient) {
    http.get(`${environment.baseURL}/data_models`)
      .subscribe((models: any) => {
        this.dataModels = models.results;
        http.get(`${environment.baseURL}/data_types`)
        .subscribe((types: any) => {
          this.dataTypes = types.results;
          this.dataTypeSub.next(this.dataTypes);
          this.dataTypes.forEach((dataType: any) => {
            const dataModel = this.dataModels[dataType.dataModel];
            this.dataTypeHash[dataType.dataType] = dataModel.properties;
          });
        });
      });
    http.get(`${environment.baseURL}/search_operations`)
      .subscribe((operations: any) => {
        this.operators = operations.results;
      });
  }

  getCurrentObject() {
    return this.queryBuilderObject;
  }

  resetObject() {
    this.queryBuilderObject = new QueryBuilder();
  }

  submitSearchResultsFromHome(queryMatch: QueryMatch) {
    this.queryBuilderObject = new QueryBuilder();
    this.queryBuilderObject.queryMatch = queryMatch;
  }

  testQueryBuilder() {
    console.log('TESTING SERVICE', this.queryBuilderObject);
  }

  getSearchResults() {
    return this.http.post<any>(`${environment.baseURL}/search`, this.queryBuilderObject);
  }

  getObjectMetadata(id) {
    return this.http.get(`${environment.baseURL}/brick_metadata/${id}`);
  }

  getCoreTypeMetadata(id) {
    return this.http.get(`${environment.baseURL}/core_type_metadata/${id}`);
  }

  getDataTypes() {
    // return this.http.get(`${environment.baseURL}/data_types`);
    // return [...this.dataTypes.map((type, idx) => {
    //   return { id: idx.toString(), text: type.dataType }
    // })];
    return this.dataTypeSub.asObservable();
  }

  getAttributes(dataType) {
    // return [{id: '', text: ''}, ...this.dataTypeHash[dataType].map((att, idx) => {
    //   return {id: idx.toString(), text: att.name}
    // })]
    return this.dataTypeHash[dataType];
  }

  getDataTypeValue(value) {
    return;
  }

  getDataModels() {
    return this.http.get(`${environment.baseURL}/data_models`);
  }

  getOperators() {
    // return this.http.get(`${environment.baseURL}/search_operations`);
    return [{id: '', text: ''},...this.operators.map((op, idx) => {
      return {id: idx.toString(), text: op };
    })];
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


}
