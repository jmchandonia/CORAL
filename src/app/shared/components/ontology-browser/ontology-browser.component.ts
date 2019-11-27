import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { UploadService } from '../../services/upload.service';
import * as $ from 'jquery';
import 'datatables.net-bs4';
import 'datatables.net';

@Component({
  selector: 'app-ontology-browser',
  templateUrl: './ontology-browser.component.html',
  styleUrls: ['./ontology-browser.component.css']
})
export class OntologyBrowserComponent implements OnInit {

  public ontologies: any[];
  dataTables: any;

  constructor(
    private uploadService: UploadService,
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.uploadService.getMicroTypes()
      .subscribe((res: any) => {
        this.ontologies = res.results;
        this.chRef.detectChanges();
        const table: any = $('table');
        this.dataTables = table.DataTable();
      });
  }

}
