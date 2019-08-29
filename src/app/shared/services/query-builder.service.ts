import { Injectable } from '@angular/core';
import { QueryBuilder, QueryMatch, QueryParam } from '../models/QueryBuilder';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class QueryBuilderService {

  private _queryBuilder: QueryBuilder;
  public queryBuilderSub = new Subject<any>();

  constructor() { }

  getQueryBuilder() {
    return this._queryBuilder;
  }
}
