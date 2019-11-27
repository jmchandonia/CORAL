import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import * as $ from 'jquery';
import 'datatables.net-bs4';
import 'datatables.net';
//// temporary import ////
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-ontology-browser',
  templateUrl: './ontology-browser.component.html',
  styleUrls: ['./ontology-browser.component.css']
})
export class OntologyBrowserComponent implements OnInit {

  public ontologies: any[];
  dataTables: any;

  constructor(
    //// temporary injection ////
    private http: HttpClient,
    /////////////////////////////
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.http.get('https://jsonplaceholder.typicode.com/posts')
      .subscribe((res: any) => {
        console.log('RES', res);
        this.ontologies = res;
        this.ontologies.forEach(ontology => {
          if (ontology.title.length > 30) { ontology.title = ontology.title.slice(0, 30); }
          ontology.valid_for_properties = Math.floor(Math.random() * 10) % 2 === 0;
          ontology.valid_for_dim_vars = Math.floor(Math.random() * 10) % 2 === 0;
          ontology.valid_for_data_vars = Math.floor(Math.random() * 10) % 2 === 0;
        });
        this.chRef.detectChanges();
        const table: any = $('table');
        this.dataTables = table.DataTable();
      });
  }

}
