import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { UploadService } from 'src/app/shared/services/upload.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { ColumnMode } from '@swimlane/ngx-datatable';

@Component({
  selector: 'app-core-type-result',
  templateUrl: './core-type-result.component.html',
  styleUrls: ['./core-type-result.component.css']
})
export class CoreTypeResultComponent implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
    private chRef: ChangeDetectorRef
  ) { }

  private batchId: string;
  columnMode= ColumnMode;

  // TODO: figure out a way to have less variables for this

  public errorResults: any[];
  public errorResultFields: any[];

  public successResults: any[];
  public successResultFields: any[] = [];

  public warningResults: any[];
  warningResultFields: any[];

  ngOnInit(): void {
    this.spinner.show('spinner')
    this.route.params.subscribe(params => {
      this.batchId = params['batchId'];
      this.uploadService.getCoreTypeUploadResults(this.batchId)
        .subscribe(({results}) => {
          this.errorResults = results['errors'];
          if (this.errorResults.length) {
            this.errorResultFields = Object.keys(results['errors'][0]['data']).map(d => ({prop: d, name: d}));
          }

          this.successResults = results['success'];
          if (this.successResults.length) {
            this.successResultFields = Object.keys(results['success'][0]).map(d => ({prop: d, name: d}))
          }

          this.warningResults = results['warnings'];
          if (this.warningResults.length) {
            this.warningResultFields = Object.keys(results['warnings'][0]['old_data']).map(d => ({prop: d, name: d}))
          }

          this.spinner.hide('spinner');
          this.chRef.detectChanges();
        }, e => console.log(e));
    });
  }

}
