import { Component, OnInit, OnDestroy } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, DimensionVariable, TypedProperty, Term } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit, OnDestroy {

  brick: Brick;
  dimVars: DimensionVariable[] = [];
  testArray = [];
  mapped = false;
  loading = false;
  error = false;
  errorSub: Subscription;


  // for testing only //

  testDimension: BrickDimension;
  testDimVar: DimensionVariable;

/////////////////////////

  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
    private validator: UploadValidationService
    ) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    // this.brick.dimensions.forEach(dim => {
    //   this.dimVars = [...this.dimVars, ...dim.variables];
    // });

    // for testing only //

    this.testDimension = new BrickDimension(this.brick, 0);
    this.testDimension.type = new Term('dimension', 'dimension');

    for (let i = 0; i < 5; i++) {
      const dv = new DimensionVariable(this.testDimension, i);
      dv.type = new Term('abc', '123');
      dv.units = new Term('abc', '123');
      dv.totalCount = Math.floor(Math.random() * 100);
      this.dimVars.push(dv);
    }

    //////////////////////

    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  testMap() {
    this.loading = true;
    this.dimVars.forEach((_, i) => {
      this.spinner.show(i.toString());
    });
    setTimeout(() => {
      this.testArray = this.dimVars.map(() => Math.floor(Math.random() * 3 ) + 1);
      this.dimVars.forEach((dimVar, idx) => {
        // dimVar.totalCount = 100;
        switch(this.testArray[idx]) {
          case 1:
            dimVar.mappedCount = dimVar.totalCount;
            break;
          case 2:
            dimVar.mappedCount = dimVar.totalCount - 5;
            break;
          case 3:
            dimVar.mappedCount = 0;
            break;
          default:
            dimVar.mappedCount = 0;
        }
      });
      this.brick.dataValues.forEach(dataValue => {
        dataValue.totalCount = 100;
        dataValue.mappedCount = Math.floor(Math.random() * 2) === 0 ? 100 : 0;
      });
      this.loading = false;
      // this.spinner.hide();
      this.dimVars.forEach((_, i) => {
        this.spinner.hide(i.toString());
      })
      this.mapped = true;
    }, 1000);
  }

  getMappedStatus(mapped, total) {
    if (mapped === total) {
      return 'status-column-success';
    }
    return mapped === 0 ? 'status-column-fail' : 'status-column-warn';
  }

}
