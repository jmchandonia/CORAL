import { Component, OnInit, OnDestroy } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension } from 'src/app/shared/models/brick';
import { Subscription } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

@Component({
  selector: 'app-dimension-builder',
  templateUrl: './dimension-builder.component.html',
  styleUrls: ['./dimension-builder.component.css']
})
export class DimensionBuilderComponent implements OnInit, OnDestroy {

  brick: Brick;
  error = false;
  errorSub: Subscription;

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  addDimension() {
    this.brick.dimensions.push(new BrickDimension(this.brick, this.brick.dimensions.length, false));
  }

  removeDimension(dimension) {
    this.brick.dimensions = this.brick.dimensions.filter(dim => dim !== dimension);
    this.brick.resetDimensionIndices();
  }

}
