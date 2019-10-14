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
  public queryBuilderSub = new Subject<QueryBuilder>();
  resultSub = new Subject();
  searchType: string;

  constructor(private http: HttpClient) { }

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
    return this.http.get(`${environment.baseURL}/data_types`);
  }

  getDataModels() {
    return this.http.get(`${environment.baseURL}/data_models`);
  }

  getOperators() {
    return this.http.get(`${environment.baseURL}/search_operations`);
  }

  getSearchType() {
    return this.searchType;
  }

  setSearchType(searchType: string) {
    this.searchType = searchType;
  }


}
