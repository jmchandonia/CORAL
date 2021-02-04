import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { DimensionVariablePreviewComponent } from './dimension-variable-preview.component';
import { BsModalRef } from 'ngx-bootstrap/modal';

describe('DimensionVariablePreviewComponent', () => {

  let spectator: Spectator<DimensionVariablePreviewComponent>;
  const createComponent = createComponentFactory({
    component: DimensionVariablePreviewComponent,
    providers: [
      BsModalRef
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      data: {
        dim_vars: [],
        size: 3,
        max_row_count: 4
      },
      title: 'test dim var preview',
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
