import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private networkSub: Subject<any> = new Subject();

  private dataModelStore = {
    queryMatch: [],
    connectsUpTo: [],
    connectsDownTo: [],
  }

  constructor(private _http: HttpClient) { }

  getDataModelProperties(dataModel, connection) {
    this._http.get('https://jsonplaceholder.typicode.com/posts')
    .subscribe(results => {
      this.dataModelStore[connection] = results;
      this.networkSub.next({
        connection: connection,
        results: results
      })
    });
  }

  submitQuery() {
    return this._http.get('https://jsonplaceholder.typicode.com/posts');
  }

  getPropertyValuesDirect(connection) {
    return connection ? 
      this.dataModelStore[connection]
      : this.dataModelStore.queryMatch;
  }

  getPropertyValues() {
    return this.networkSub.asObservable();
  }


}
