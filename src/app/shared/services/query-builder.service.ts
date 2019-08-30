import { Injectable } from '@angular/core';
import { QueryBuilder, QueryMatch, QueryParam } from '../models/QueryBuilder';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class QueryBuilderService {

  private queryBuilderObject: QueryBuilder = new QueryBuilder();
  public queryBuilderSub = new Subject<QueryBuilder>();

  constructor() { }

  getCurrentObject() {
    if (!this.queryBuilderObject) {
      this.queryBuilderObject = new QueryBuilder();
      return this.queryBuilderObject;
    } else {
      return this.queryBuilderObject;
    }
  }

  getUpdatedObject() {
    return this.queryBuilderSub.asObservable();
  }

  updateQueryMatch(connection, queryMatch) {
    this.queryBuilderObject[connection] = queryMatch;
  }


}
