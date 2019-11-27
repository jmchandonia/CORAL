import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { UploadService } from '../../services/upload.service';
import * as $ from 'jquery';
import 'datatables.net-bs4';
import 'datatables.net';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-microtype-browser',
  templateUrl: './microtype-browser.component.html',
  styleUrls: ['./microtype-browser.component.css']
})
export class MicrotypeBrowserComponent implements OnInit {

  public microtypes: any[];
  dataTables: any;

  constructor(
    private uploadService: UploadService,
    private chRef: ChangeDetectorRef,
    private spinner: NgxSpinnerService
  ) { }

  ngOnInit() {
    this.spinner.show('spinner');
    this.uploadService.getMicroTypes()
      .subscribe((res: any) => {
        this.spinner.hide('spinner');
        this.microtypes = res.results;
        this.chRef.detectChanges();
        const table: any = $('table');
        this.dataTables = table.DataTable();
      });
  }

}
