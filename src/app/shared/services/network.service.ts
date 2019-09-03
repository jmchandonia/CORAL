import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private networkSub: Subject<any> = new Subject();

  private dataTypeStore = {
    queryMatch: [],
    connectsUpTo: [],
    connectsDownTo: [],
  }

  constructor(private _http: HttpClient) { }

  getDataTypeProperties(dataType, connection) {
    this._http.get('https://jsonplaceholder.typicode.com/posts')
    .subscribe(results => {
      this.dataTypeStore[connection] = results;
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
      this.dataTypeStore[connection]
      : this.dataTypeStore.queryMatch;
  }

  getPropertyValues() {
    return this.networkSub.asObservable();
  }


}
